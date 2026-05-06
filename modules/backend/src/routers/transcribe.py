"""
Router principal de transcrição de áudio.

As chamadas síncronas de ML (diarize, transcribe_segment) são despachadas para
o thread-pool padrão do asyncio via loop.run_in_executor, liberando o event
loop para responder a outros requests durante o processamento.

Leituras dos engines (is not None) não precisam do mutation_lock — são operações
atômicas no nível do GIL.  Apenas POST /api-keys muta os engines.
"""

import asyncio
import logging
import time
import uuid
from functools import partial
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import engine_registry
from ..authorization import create_transcription_owner, enforce_transcription_access
from ..config import settings
from ..database import SessionLocal, get_db
from ..models import Transcription, TranscriptionJob
from ..security import TokenData, require_scope_when
from ..utils.audio import convert_to_wav, remove_temp_file_with_retry

logger = logging.getLogger(__name__)

router = APIRouter()

_job_queue: asyncio.Queue[Optional[int]] = asyncio.Queue()
_worker_task: Optional[asyncio.Task] = None


async def start_transcription_worker():
    """Inicia worker local de processamento assíncrono, se ainda não estiver rodando."""
    global _worker_task
    if _worker_task and not _worker_task.done():
        return
    _worker_task = asyncio.create_task(_transcription_worker_loop())
    logger.info("Transcription worker started")


async def stop_transcription_worker():
    """Encerra worker local de transcrição de forma graciosa."""
    global _worker_task
    if not _worker_task:
        return

    await _job_queue.put(None)
    await _worker_task
    _worker_task = None
    logger.info("Transcription worker stopped")


async def recover_pending_transcription_jobs():
    """Reenfileira jobs pendentes (queued/processing) após restart do processo."""
    db = SessionLocal()
    try:
        pending_jobs = (
            db.query(TranscriptionJob)
            .filter(TranscriptionJob.status.in_(["queued", "processing"]))
            .all()
        )

        for job in pending_jobs:
            job.status = "queued"
            await _job_queue.put(job.transcription_id)

        db.commit()
        if pending_jobs:
            logger.info(f"Recovered {len(pending_jobs)} pending transcription jobs")
    finally:
        db.close()


async def get_transcription_job_queue_size() -> int:
    return _job_queue.qsize()


async def enqueue_transcription_job(transcription_id: int):
    await _job_queue.put(transcription_id)


async def _transcription_worker_loop():
    """Loop do worker local: consome fila e processa jobs de transcrição."""
    while True:
        transcription_id = await _job_queue.get()
        if transcription_id is None:
            _job_queue.task_done()
            break

        try:
            await _process_transcription_job(transcription_id)
        except Exception as e:
            logger.exception(f"Unhandled worker error for transcription {transcription_id}: {e}")
        finally:
            _job_queue.task_done()


async def _process_transcription_job(transcription_id: int):
    """Processa um job de transcrição pendente e persiste o resultado."""
    db = SessionLocal()
    temp_wav_path: Optional[str] = None
    input_path: Optional[str] = None

    try:
        job = (
            db.query(TranscriptionJob)
            .filter(TranscriptionJob.transcription_id == transcription_id)
            .first()
        )
        transcription = (
            db.query(Transcription)
            .filter(Transcription.id == transcription_id)
            .first()
        )

        if not job or not transcription:
            logger.warning(f"Job or transcription not found for id={transcription_id}")
            return

        if job.status == "done":
            return

        start_time = time.time()
        loop = asyncio.get_running_loop()
        input_path = job.input_path

        job.status = "processing"
        transcription.status = "processing"
        db.commit()

        wav_output_path = f"temp/wav_{uuid.uuid4()}.wav"
        temp_wav_path, duration = await loop.run_in_executor(
            None,
            convert_to_wav,
            input_path,
            wav_output_path,
        )

        if job.use_diarization:
            segments, num_speakers = await _process_with_diarization(
                temp_wav_path,
                job.transcription_model,
                loop,
            )
        else:
            segments, num_speakers = await _process_without_diarization(
                temp_wav_path,
                duration,
                job.transcription_model,
                loop,
            )

        word_count = sum(len(seg["text"].split()) for seg in segments)
        processing_time = time.time() - start_time

        transcription.duration_seconds = duration
        transcription.transcription_model = job.transcription_model
        transcription.use_diarization = job.use_diarization
        transcription.segments = segments
        transcription.num_speakers = num_speakers
        transcription.word_count = word_count
        transcription.processing_time_seconds = processing_time
        transcription.status = "completed"
        transcription.error_message = None

        job.status = "done"
        job.error_message = None
        db.commit()

    except Exception as e:
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
        if transcription:
            transcription.status = "failed"
            transcription.error_message = str(e)
        if job:
            job.status = "failed"
            job.error_message = str(e)
        db.commit()
        logger.error(f"Error processing async transcription job {transcription_id}: {e}")

    finally:
        await remove_temp_file_with_retry(input_path)
        await remove_temp_file_with_retry(temp_wav_path)
        db.close()


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    use_diarization: bool = Form(False),
    transcription_model: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(
        require_scope_when("transcribe", settings.AUTH_PROTECT_PROCESSING)
    ),
):
    """
    Transcreve um arquivo de áudio usando os engines integrados.

    Args:
        file:               Arquivo de áudio.
        use_diarization:    Se deve usar diarização de falantes (Pyannote).
        transcription_model: Modelo de transcrição ("whisper" ou "assemblyai").

    Returns:
        Resultado da transcrição com segmentos e metadados.
    """
    start_time = time.time()
    temp_input_path: Optional[str] = None
    temp_wav_path: Optional[str] = None

    try:
        # ---- Validar extensão ----
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in settings.allowed_extensions_list:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File extension '{file_ext}' not allowed. "
                    f"Allowed: {settings.ALLOWED_EXTENSIONS}"
                ),
            )

        # ---- Salvar upload com nome único ----
        unique_name = f"upload_{uuid.uuid4()}.{file_ext}"
        temp_input_path = f"temp/{unique_name}"
        async with aiofiles.open(temp_input_path, "wb") as f:
            content = await file.read()

            if len(content) > settings.max_upload_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum allowed ({settings.MAX_UPLOAD_SIZE_MB} MB)",
                )

            await f.write(content)

        file_size_mb = len(content) / (1024 * 1024)

        # ---- Converter para WAV (I/O-bound via pydub/ffmpeg, em executor) ----
        wav_output_path = f"temp/wav_{uuid.uuid4()}.wav"
        loop = asyncio.get_event_loop()
        temp_wav_path, duration = await loop.run_in_executor(
            None, convert_to_wav, temp_input_path, wav_output_path
        )

        logger.info(
            f"Processing file: {file.filename} ({file_size_mb:.2f} MB, {duration:.2f}s)"
        )

        # ---- Selecionar modelo ----
        if not transcription_model:
            transcription_model = "whisper" if engine_registry.whisper_engine else "assemblyai"

        # ---- Criar registro inicial no banco ----
        transcription_record = Transcription(
            filename=file.filename,
            original_filename=file.filename,
            file_size_mb=file_size_mb,
            duration_seconds=duration,
            transcription_model=transcription_model,
            use_diarization=use_diarization,
            status="processing",
            segments=[],
        )
        db.add(transcription_record)
        db.commit()
        db.refresh(transcription_record)

        create_transcription_owner(db, transcription_record.id, current_user)

        # ---- Processar áudio ----
        try:
            segments: list = []
            num_speakers: int = 0

            if use_diarization:
                segments, num_speakers = await _process_with_diarization(
                    temp_wav_path, transcription_model, loop
                )
            else:
                segments, num_speakers = await _process_without_diarization(
                    temp_wav_path, duration, transcription_model, loop
                )

            word_count = sum(len(seg["text"].split()) for seg in segments)
            processing_time = time.time() - start_time

            # ---- Persistir resultado ----
            transcription_record.segments = segments
            transcription_record.num_speakers = num_speakers
            transcription_record.word_count = word_count
            transcription_record.processing_time_seconds = processing_time
            transcription_record.status = "completed"
            db.commit()

            logger.info(f"Transcription completed in {processing_time:.2f}s")

            return {
                "id": transcription_record.id,
                "segments": segments,
                "num_speakers": num_speakers,
                "word_count": word_count,
                "duration": duration,
                "model": transcription_model,
                "diarization": use_diarization,
                "processing_time": processing_time,
            }

        except HTTPException:
            raise

        except Exception as e:
            transcription_record.status = "failed"
            transcription_record.error_message = str(e)
            db.commit()
            raise

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error processing transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        await file.close()
        await remove_temp_file_with_retry(temp_input_path)
        await remove_temp_file_with_retry(temp_wav_path)


@router.post("/transcriptions/jobs", status_code=202)
async def create_transcription_job(
    file: UploadFile = File(...),
    use_diarization: bool = Form(False),
    transcription_model: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(
        require_scope_when("transcribe", settings.AUTH_PROTECT_PROCESSING)
    ),
):
    """Cria um job local assíncrono de transcrição e retorna imediatamente."""
    temp_input_path: Optional[str] = None

    try:
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in settings.allowed_extensions_list:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File extension '{file_ext}' not allowed. "
                    f"Allowed: {settings.ALLOWED_EXTENSIONS}"
                ),
            )

        unique_name = f"upload_{uuid.uuid4()}.{file_ext}"
        temp_input_path = f"temp/{unique_name}"
        async with aiofiles.open(temp_input_path, "wb") as f:
            content = await file.read()
            if len(content) > settings.max_upload_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum allowed ({settings.MAX_UPLOAD_SIZE_MB} MB)",
                )
            await f.write(content)

        file_size_mb = len(content) / (1024 * 1024)

        if not transcription_model:
            transcription_model = "whisper" if engine_registry.whisper_engine else "assemblyai"

        transcription_record = Transcription(
            filename=file.filename,
            original_filename=file.filename,
            file_size_mb=file_size_mb,
            duration_seconds=0.0,
            transcription_model=transcription_model,
            use_diarization=use_diarization,
            status="queued",
            segments=[],
        )
        db.add(transcription_record)
        db.commit()
        db.refresh(transcription_record)

        create_transcription_owner(db, transcription_record.id, current_user)

        job = TranscriptionJob(
            transcription_id=transcription_record.id,
            input_path=temp_input_path,
            use_diarization=use_diarization,
            transcription_model=transcription_model,
            status="queued",
        )
        db.add(job)
        db.commit()

        await enqueue_transcription_job(transcription_record.id)

        return {
            "id": transcription_record.id,
            "status": "queued",
            "message": "Transcription job queued successfully",
            "status_url": f"/transcriptions/jobs/{transcription_record.id}/status",
            "result_url": f"/transcriptions/{transcription_record.id}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transcription job: {e}")
        await remove_temp_file_with_retry(temp_input_path)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()


@router.get("/transcriptions/jobs/{transcription_id}/status")
async def get_transcription_job_status(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(
        require_scope_when("read_transcriptions", settings.AUTH_PROTECT_READS)
    ),
):
    """Consulta status do job de transcrição assíncrono local."""
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    if settings.AUTH_PROTECT_READS:
        enforce_transcription_access(db, transcription_id, current_user, write=False)

    job = (
        db.query(TranscriptionJob)
        .filter(TranscriptionJob.transcription_id == transcription_id)
        .first()
    )

    return {
        "id": transcription_id,
        "transcription_status": transcription.status,
        "job_status": job.status if job else None,
        "error_message": transcription.error_message or (job.error_message if job else None),
        "queue_size": await get_transcription_job_queue_size(),
        "completed": transcription.status == "completed",
        "failed": transcription.status == "failed",
    }


# ---------------------------------------------------------------------------
# Helpers de processamento (privados)
# ---------------------------------------------------------------------------

async def _process_with_diarization(
    wav_path: str,
    transcription_model: str,
    loop: asyncio.AbstractEventLoop,
) -> tuple[list, int]:
    """Executa diarização e transcrição de cada segmento no thread-pool."""
    if not engine_registry.diarization_engine:
        raise HTTPException(
            status_code=503,
            detail="Diarization engine not loaded. Check HF_TOKEN configuration.",
        )

    # Diarização — síncrona, pesada → thread-pool
    logger.info("Executando diarização...")
    diarization_result = await loop.run_in_executor(
        None, engine_registry.diarization_engine.diarize, wav_path
    )
    diar_segments = diarization_result["segments"]
    num_speakers = diarization_result["num_speakers"]
    logger.info(
        f"Diarização concluída: {len(diar_segments)} segmentos, {num_speakers} falantes"
    )

    # Selecionar função de transcrição
    transcribe_func = _get_transcribe_func(transcription_model)

    # Transcrever cada segmento no thread-pool
    segments: list = []
    for seg in diar_segments:
        try:
            fn = partial(transcribe_func, wav_path, start=seg["start"], end=seg["end"])
            text = await loop.run_in_executor(None, fn)
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "speaker": seg["speaker"],
                "text": text,
            })
        except Exception as e:
            logger.warning(
                f"Erro ao transcrever segmento {seg['start']:.2f}-{seg['end']:.2f}: {e}"
            )
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "speaker": seg["speaker"],
                "text": "[erro na transcrição]",
            })

    return segments, num_speakers


async def _process_without_diarization(
    wav_path: str,
    duration: float,
    transcription_model: str,
    loop: asyncio.AbstractEventLoop,
) -> tuple[list, int]:
    """Transcreve o arquivo inteiro no thread-pool, sem diarização."""
    transcribe_func = _get_transcribe_func(transcription_model)

    logger.info(f"Transcrevendo com {transcription_model} (sem diarização)...")
    fn = partial(transcribe_func, wav_path)
    text = await loop.run_in_executor(None, fn)

    segments = [{
        "start": 0.0,
        "end": duration,
        "speaker": "SPEAKER_00",
        "text": text,
    }]
    return segments, 1


def _get_transcribe_func(transcription_model: str):
    """Retorna a função de transcrição do engine correto ou levanta HTTPException."""
    if transcription_model == "whisper":
        if not engine_registry.whisper_engine:
            raise HTTPException(
                status_code=503,
                detail="Whisper engine not loaded. Check HF_TOKEN configuration.",
            )
        return engine_registry.whisper_engine.transcribe_segment

    if transcription_model == "assemblyai":
        if not engine_registry.assemblyai_engine:
            raise HTTPException(
                status_code=503,
                detail="AssemblyAI engine not loaded. Check AAI_API_KEY configuration.",
            )
        return engine_registry.assemblyai_engine.transcribe_segment

    raise HTTPException(
        status_code=400,
        detail=f"Unknown transcription model: {transcription_model}",
    )
