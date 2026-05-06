from typing import Optional
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_
import aiofiles

from ..authorization import enforce_transcription_access, is_admin, create_transcription_owner
from ..database import get_db
from ..models import Transcription, TranscriptionOwnership, TranscriptionJob
from ..config import settings
from ..schemas import JobResponse, JobStatusResponse
from ..security import TokenData, require_scope_when
from ..workers.config import is_redis_available

# Importa RQ se Redis estiver disponível
if is_redis_available():
    from rq import Queue
    from redis import Redis as RedisClient
    _redis_conn = None
    _rq_queue = None
    
    def get_rq_queue():
        global _redis_conn, _rq_queue
        if _rq_queue is None:
            _redis_conn = RedisClient.from_url(settings.REDIS_URL, decode_responses=False)
            _rq_queue = Queue("transcriptions", connection=_redis_conn)
        return _rq_queue
else:
    _rq_queue = None
    def get_rq_queue():
        return None

router = APIRouter()


@router.get("/transcriptions")
async def list_transcriptions(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(
        require_scope_when("read_transcriptions", settings.AUTH_PROTECT_READS)
    ),
):
    """
    Lista transcrições com paginação opcional.

    Args:
        skip:   Registros a pular.
        limit:  Máximo de registros a retornar.
        status: Filtrar por status (processing, completed, failed).
    """
    query = db.query(Transcription)

    if settings.AUTH_PROTECT_READS and current_user and not is_admin(current_user):
        query = query.outerjoin(
            TranscriptionOwnership,
            TranscriptionOwnership.transcription_id == Transcription.id,
        )

        if settings.is_auth_strict:
            query = query.filter(TranscriptionOwnership.owner_sub == current_user.username)
        else:
            query = query.filter(
                or_(
                    TranscriptionOwnership.owner_sub == current_user.username,
                    TranscriptionOwnership.owner_sub.is_(None),
                )
            )

    if status:
        query = query.filter(Transcription.status == status)

    total = query.count()
    transcriptions = (
        query.order_by(Transcription.created_at.desc()).offset(skip).limit(limit).all()
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "transcriptions": [t.to_dict() for t in transcriptions],
    }


@router.get("/transcriptions/{transcription_id}")
async def get_transcription(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(
        require_scope_when("read_transcriptions", settings.AUTH_PROTECT_READS)
    ),
):
    """Obtém detalhes de uma transcrição específica."""
    transcription = (
        db.query(Transcription).filter(Transcription.id == transcription_id).first()
    )

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    if settings.AUTH_PROTECT_READS:
        enforce_transcription_access(db, transcription_id, current_user, write=False)

    return transcription.to_dict()


@router.delete("/transcriptions/{transcription_id}")
async def delete_transcription(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(
        require_scope_when("delete_transcriptions", settings.AUTH_PROTECT_PROCESSING)
    ),
):
    """Remove uma transcrição."""
    transcription = (
        db.query(Transcription).filter(Transcription.id == transcription_id).first()
    )

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    if settings.AUTH_PROTECT_PROCESSING:
        enforce_transcription_access(db, transcription_id, current_user, write=True)

    db.delete(transcription)
    db.commit()

    return {"message": "Transcription deleted successfully"}


@router.get("/stats")
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(
        require_scope_when("read_transcriptions", settings.AUTH_PROTECT_READS)
    ),
):
    """Obtém estatísticas gerais do sistema."""
    total_transcriptions = db.query(Transcription).count()
    completed = db.query(Transcription).filter(Transcription.status == "completed").count()
    failed = db.query(Transcription).filter(Transcription.status == "failed").count()
    processing = db.query(Transcription).filter(Transcription.status == "processing").count()

    return {
        "total_transcriptions": total_transcriptions,
        "completed": completed,
        "failed": failed,
        "processing": processing,
    }


@router.post("/transcriptions/jobs", response_model=JobResponse, status_code=202)
async def create_transcription_job(
    file: UploadFile = File(...),
    use_diarization: bool = Form(False),
    transcription_model: str = Form("whisper"),
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(
        require_scope_when("process", settings.AUTH_PROTECT_PROCESSING)
    ),
):
    """
    Enfileira um novo job de transcrição (assíncrono).
    
    Retorna 202 (Accepted) imediatamente com o ID do job.
    O processamento acontece em segundo plano.
    
    Args:
        file: Arquivo de áudio para transcrever
        use_diarization: Se deve detectar múltiplos falantes
        transcription_model: Modelo a usar ("whisper" ou "assemblyai")
        
    Returns:
        JobResponse com URLs de status e resultado
    """
    # Verifica Redis disponível
    if not is_redis_available():
        raise HTTPException(
            status_code=503,
            detail="Redis não está disponível. Execute 'run_worker.py' em outro terminal."
        )
    
    # Valida modelo
    valid_models = ["whisper", "assemblyai"]
    if transcription_model not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Modelo inválido. Use um de: {', '.join(valid_models)}"
        )
    
    # Cria diretórios se não existirem
    os.makedirs("temp", exist_ok=True)
    os.makedirs("database", exist_ok=True)
    
    # Gera UUID e caminho para arquivo
    file_uuid = str(uuid.uuid4())
    file_path = f"database/{file_uuid}_{file.filename}"
    
    try:
        # Salva arquivo no disco
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        # Calcula tamanho do arquivo em MB
        file_size_mb = len(content) / (1024 * 1024)
        
        # Cria registro Transcription
        transcription = Transcription(
            filename=file_uuid,
            original_filename=file.filename or "unknown",
            file_size_mb=file_size_mb,
            duration_seconds=0.0,  # Será calculado durante processamento
            transcription_model=transcription_model,
            use_diarization=use_diarization,
            segments=[],
            status="queued",
        )
        db.add(transcription)
        db.flush()  # Obtém o ID gerado
        transcription_id = transcription.id
        
        # Cria registro TranscriptionJob
        job = TranscriptionJob(
            transcription_id=transcription_id,
            input_path=file_path,
            use_diarization=use_diarization,
            transcription_model=transcription_model,
            status="queued",
        )
        db.add(job)
        db.commit()
        
        # Registra ownership se auth está ativada
        if settings.AUTH_PROTECT_PROCESSING and current_user:
            create_transcription_owner(db, transcription_id, current_user.username)
        
        # Enfileira job no RQ
        from src.workers.transcription_worker import process_transcription_job_sync
        rq_queue = get_rq_queue()
        rq_job = rq_queue.enqueue(
            process_transcription_job_sync,
            transcription_id,
            job_id=f"transcription_{transcription_id}",
        )
        
        # Retorna resposta
        return JobResponse(
            transcription_id=transcription_id,
            status_url=f"/transcriptions/{transcription_id}",
            result_url=f"/transcriptions/{transcription_id}",
            message="Job enfileirado com sucesso. Acesse status_url para acompanhar."
        )
        
    except Exception as e:
        # Remove arquivo em caso de erro
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao enfileirar job: {str(e)}"
        )


@router.get("/transcriptions/{transcription_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(
        require_scope_when("read_transcriptions", settings.AUTH_PROTECT_READS)
    ),
):
    """
    Obtém o status atual de um job de transcrição.
    
    Args:
        transcription_id: ID da transcrição
        
    Returns:
        JobStatusResponse com status do job e transcrição
    """
    # Obtém registros
    transcription = (
        db.query(Transcription)
        .filter(Transcription.id == transcription_id)
        .first()
    )
    job = (
        db.query(TranscriptionJob)
        .filter(TranscriptionJob.transcription_id == transcription_id)
        .first()
    )
    
    if not transcription or not job:
        raise HTTPException(status_code=404, detail="Transcrição ou job não encontrado")
    
    if settings.AUTH_PROTECT_READS:
        enforce_transcription_access(db, transcription_id, current_user, write=False)
    
    # Obtém tamanho da fila se Redis está disponível
    queue_size = 0
    if is_redis_available():
        try:
            rq_queue = get_rq_queue()
            queue_size = len(rq_queue)
        except:
            pass
    
    return JobStatusResponse(
        transcription_id=transcription_id,
        transcription_status=transcription.status,
        job_status=job.status,
        queue_size=queue_size,
        error_message=transcription.error_message,
        processing_time_seconds=transcription.processing_time_seconds,
        word_count=transcription.word_count,
        num_speakers=transcription.num_speakers,
    )
