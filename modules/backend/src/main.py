import logging
import os
import time
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydub import AudioSegment
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import aiofiles

from .config import settings
from .models import Base, Transcription
from .security import get_current_user, TokenData
from .services.diarization_engine import DiarizationEngine
from .services.transcription_engine import WhisperEngine, AssemblyAIEngine
from .services.meeting_minutes import MeetingMinutesGenerator
from .utils.gpu_utils import log_device_info, optimize_gpu_settings
from .api_keys_manager import api_keys_manager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Transcription API - All Services Integrated",
    description="API de transcrição de áudio com diarização de falantes (Whisper, AssemblyAI, Pyannote) - Tudo em um processo no port 2020",
    version="2.0.0",
    debug=settings.DEBUG
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar banco de dados
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar tabelas
Base.metadata.create_all(bind=engine)

# Criar diretórios necessários
os.makedirs("database", exist_ok=True)
os.makedirs("temp", exist_ok=True)

# ========== MODELOS GLOBAIS ==========
diarization_engine: Optional[DiarizationEngine] = None
whisper_engine: Optional[WhisperEngine] = None
assemblyai_engine: Optional[AssemblyAIEngine] = None
meeting_minutes_generator: Optional[MeetingMinutesGenerator] = None

# ========== PYDANTIC MODELS ==========
class ApiKeysUpdate(BaseModel):
    hf_token: Optional[str] = None
    aai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

class MeetingMinutesRequest(BaseModel):
    transcription_id: int
    title: Optional[str] = None
    date: Optional[str] = None
    participants: Optional[List[str]] = None

@app.on_event("startup")
async def load_models():
    """Carrega todos os modelos ML no startup da aplicação."""
    global diarization_engine, whisper_engine, assemblyai_engine, meeting_minutes_generator
    
    logger.info("=" * 60)
    logger.info("INICIANDO CARREGAMENTO DOS MODELOS")
    logger.info("=" * 60)
    
    # Carregar chaves salvas do gerenciador
    saved_keys = api_keys_manager.get_all()
    if saved_keys.get("HF_TOKEN"):
        settings.HF_TOKEN = saved_keys["HF_TOKEN"]
        os.environ["HF_TOKEN"] = saved_keys["HF_TOKEN"]
        logger.info("🔑 HF_TOKEN carregado do armazenamento persistente")
    
    if saved_keys.get("AAI_API_KEY"):
        settings.AAI_API_KEY = saved_keys["AAI_API_KEY"]
        os.environ["AAI_API_KEY"] = saved_keys["AAI_API_KEY"]
        logger.info("🔑 AAI_API_KEY carregado do armazenamento persistente")
    
    if saved_keys.get("GEMINI_API_KEY"):
        settings.GEMINI_API_KEY = saved_keys.get("GEMINI_API_KEY", "")
        os.environ["GEMINI_API_KEY"] = saved_keys["GEMINI_API_KEY"]
        logger.info("🔑 GEMINI_API_KEY carregado do armazenamento persistente")
    
    # Log de informações do dispositivo
    log_device_info()
    
    # Aplicar otimizações de GPU/CPU
    optimize_gpu_settings()
    
    # Carregar Pyannote (Diarização)
    if settings.HF_TOKEN:
        try:
            logger.info("🎯 Carregando Pyannote para diarização...")
            diarization_engine = DiarizationEngine(settings.HF_TOKEN)
            logger.info(f"✅ Pyannote carregado! Device: {diarization_engine.get_device()}")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar Pyannote: {e}")
            logger.warning("⚠️  Diarização não estará disponível")
    else:
        logger.warning("⚠️  HF_TOKEN não configurado - Pyannote não será carregado")
    
    # Carregar Whisper (Transcrição Local)
    if settings.HF_TOKEN:
        try:
            logger.info("🎯 Carregando Whisper para transcrição local...")
            whisper_engine = WhisperEngine(settings.HF_TOKEN)
            logger.info(f"✅ Whisper carregado! Device: {whisper_engine.get_device()}")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar Whisper: {e}")
            logger.warning("⚠️  Transcrição Whisper não estará disponível")
    else:
        logger.warning("⚠️  HF_TOKEN não configurado - Whisper não será carregado")
    
    # Configurar AssemblyAI (Transcrição Cloud)
    if settings.AAI_API_KEY:
        try:
            logger.info("🎯 Configurando AssemblyAI para transcrição cloud...")
            assemblyai_engine = AssemblyAIEngine(settings.AAI_API_KEY)
            logger.info("✅ AssemblyAI configurado!")
        except Exception as e:
            logger.error(f"❌ Erro ao configurar AssemblyAI: {e}")
            logger.warning("⚠️  Transcrição AssemblyAI não estará disponível")
    else:
        logger.warning("⚠️  AAI_API_KEY não configurado - AssemblyAI não será carregado")
    
    # Configurar Gemini (Geração de Atas)
    if settings.GEMINI_API_KEY:
        try:
            logger.info("🎯 Configurando Gemini para geração de atas...")
            meeting_minutes_generator = MeetingMinutesGenerator(settings.GEMINI_API_KEY)
            logger.info("✅ Gemini configurado!")
        except Exception as e:
            logger.error(f"❌ Erro ao configurar Gemini: {e}")
            logger.warning("⚠️  Geração de atas não estará disponível")
    else:
        logger.warning("⚠️  GEMINI_API_KEY não configurado - Geração de atas não será carregado")
    
    logger.info("=" * 60)
    logger.info("MODELOS CARREGADOS - API PRONTA!")
    logger.info("=" * 60)


def get_db():
    """Dependency para obter sessão do banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def convert_to_wav(input_path: str, output_path: str = "temp/audio.wav") -> tuple[str, float]:
    """
    Converte arquivo de áudio para WAV.
    
    Returns:
        Tupla (caminho_wav, duração_segundos)
    """
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
        duration = len(audio) / 1000.0
        return output_path, duration
    except Exception as e:
        logger.error(f"Error converting to WAV: {e}")
        raise HTTPException(status_code=400, detail=f"Error converting audio: {str(e)}")


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {
        "message": "Transcription API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Verifica a saúde da API e todos os modelos carregados."""
    return {
        "status": "ok",
        "models": {
            "diarization": {
                "loaded": diarization_engine is not None,
                "device": diarization_engine.get_device() if diarization_engine else "not loaded"
            },
            "whisper": {
                "loaded": whisper_engine is not None,
                "device": whisper_engine.get_device() if whisper_engine else "not loaded"
            },
            "assemblyai": {
                "loaded": assemblyai_engine is not None,
                "device": assemblyai_engine.get_device() if assemblyai_engine else "not loaded"
            }
        },
        "database": "connected"
    }


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    use_diarization: bool = Form(False),
    transcription_model: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(get_current_user)
):
    """
    Transcreve um arquivo de áudio usando engines integrados.
    
    Args:
        file: Arquivo de áudio
        use_diarization: Se deve usar diarização de falantes (Pyannote)
        transcription_model: Modelo de transcrição ("whisper" ou "assemblyai")
        
    Returns:
        Resultado da transcrição com segmentos e metadados
    """
    start_time = time.time()
    temp_input_path = None
    temp_wav_path = None
    
    try:
        # Validar extensão do arquivo
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in settings.allowed_extensions_list:
            raise HTTPException(
                status_code=400,
                detail=f"File extension '{file_ext}' not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Salvar arquivo temporário
        temp_input_path = f"temp/{file.filename}"
        async with aiofiles.open(temp_input_path, "wb") as f:
            content = await file.read()
            
            # Verificar tamanho do arquivo
            if len(content) > settings.max_upload_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum allowed ({settings.MAX_UPLOAD_SIZE_MB} MB)"
                )
            
            await f.write(content)
        
        file_size_mb = len(content) / (1024 * 1024)
        
        # Converter para WAV
        temp_wav_path, duration = convert_to_wav(temp_input_path)
        
        logger.info(f"Processing file: {file.filename} ({file_size_mb:.2f} MB, {duration:.2f}s)")
        
        # Decidir modelo de transcrição
        if not transcription_model:
            transcription_model = "whisper" if whisper_engine else "assemblyai"
        
        # Criar registro no banco de dados
        transcription_record = Transcription(
            filename=file.filename,
            original_filename=file.filename,
            file_size_mb=file_size_mb,
            duration_seconds=duration,
            transcription_model=transcription_model,
            use_diarization=use_diarization,
            status="processing",
            segments=[]
        )
        db.add(transcription_record)
        db.commit()
        db.refresh(transcription_record)
        
        # Processar áudio
        try:
            segments = []
            num_speakers = 0
            
            if use_diarization:
                # ========== DIARIZAÇÃO + TRANSCRIÇÃO ==========
                if not diarization_engine:
                    raise HTTPException(
                        status_code=503,
                        detail="Diarization engine not loaded. Check HF_TOKEN configuration."
                    )
                
                logger.info("Executando diarização...")
                diarization_result = diarization_engine.diarize(temp_wav_path)
                diar_segments = diarization_result["segments"]
                num_speakers = diarization_result["num_speakers"]
                
                logger.info(f"Diarização concluída: {len(diar_segments)} segmentos, {num_speakers} falantes")
                
                # Escolher engine de transcrição
                if transcription_model == "whisper":
                    if not whisper_engine:
                        raise HTTPException(
                            status_code=503,
                            detail="Whisper engine not loaded. Check HF_TOKEN configuration."
                        )
                    transcribe_func = whisper_engine.transcribe_segment
                elif transcription_model == "assemblyai":
                    if not assemblyai_engine:
                        raise HTTPException(
                            status_code=503,
                            detail="AssemblyAI engine not loaded. Check AAI_API_KEY configuration."
                        )
                    transcribe_func = assemblyai_engine.transcribe_segment
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown transcription model: {transcription_model}"
                    )
                
                # Transcrever cada segmento
                for seg in diar_segments:
                    try:
                        text = transcribe_func(
                            temp_wav_path,
                            start=seg["start"],
                            end=seg["end"]
                        )
                        segments.append({
                            "start": seg["start"],
                            "end": seg["end"],
                            "speaker": seg["speaker"],
                            "text": text
                        })
                    except Exception as e:
                        logger.warning(f"Erro ao transcrever segmento {seg['start']:.2f}-{seg['end']:.2f}: {e}")
                        segments.append({
                            "start": seg["start"],
                            "end": seg["end"],
                            "speaker": seg["speaker"],
                            "text": "[erro na transcrição]"
                        })
            
            else:
                # ========== TRANSCRIÇÃO SEM DIARIZAÇÃO ==========
                if transcription_model == "whisper":
                    if not whisper_engine:
                        raise HTTPException(
                            status_code=503,
                            detail="Whisper engine not loaded. Check HF_TOKEN configuration."
                        )
                    logger.info("Transcrevendo com Whisper (sem diarização)...")
                    text = whisper_engine.transcribe_segment(temp_wav_path)
                    
                elif transcription_model == "assemblyai":
                    if not assemblyai_engine:
                        raise HTTPException(
                            status_code=503,
                            detail="AssemblyAI engine not loaded. Check AAI_API_KEY configuration."
                        )
                    logger.info("Transcrevendo com AssemblyAI (sem diarização)...")
                    text = assemblyai_engine.transcribe_segment(temp_wav_path)
                
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown transcription model: {transcription_model}"
                    )
                
                segments = [{
                    "start": 0.0,
                    "end": duration,
                    "speaker": "SPEAKER_00",
                    "text": text
                }]
                num_speakers = 1
            
            # Calcular contagem de palavras
            word_count = sum(len(seg["text"].split()) for seg in segments)
            
            # Atualizar registro
            processing_time = time.time() - start_time
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
                "processing_time": processing_time
            }
        
        except HTTPException:
            raise
        
        except Exception as e:
            # Atualizar registro com erro
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
        # Limpar arquivos temporários
        if temp_input_path and os.path.exists(temp_input_path):
            try:
                os.remove(temp_input_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_input_path}: {e}")
        
        if temp_wav_path and os.path.exists(temp_wav_path):
            try:
                os.remove(temp_wav_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_wav_path}: {e}")


@app.get("/transcriptions")
async def list_transcriptions(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(get_current_user)
):
    """
    Lista transcrições.
    
    Args:
        skip: Número de registros para pular
        limit: Número máximo de registros a retornar
        status: Filtrar por status (processing, completed, failed)
    """
    query = db.query(Transcription)
    
    if status:
        query = query.filter(Transcription.status == status)
    
    total = query.count()
    transcriptions = query.order_by(Transcription.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "transcriptions": [t.to_dict() for t in transcriptions]
    }


@app.get("/transcriptions/{transcription_id}")
async def get_transcription(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(get_current_user)
):
    """Obtém detalhes de uma transcrição específica."""
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return transcription.to_dict()


@app.delete("/transcriptions/{transcription_id}")
async def delete_transcription(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(get_current_user)
):
    """Remove uma transcrição."""
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    db.delete(transcription)
    db.commit()
    
    return {"message": "Transcription deleted successfully"}


@app.get("/stats")
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(get_current_user)
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
        "processing": processing
    }


@app.get("/api-keys")
async def get_api_keys_status(
    current_user: Optional[TokenData] = Depends(get_current_user)
):
    """Retorna o status das API Keys (sem expor os valores)."""
    return {
        "hf_token": {
            "configured": bool(settings.HF_TOKEN),
            "value": f"{settings.HF_TOKEN[:8]}..." if settings.HF_TOKEN else None
        },
        "aai_api_key": {
            "configured": bool(settings.AAI_API_KEY),
            "value": f"{settings.AAI_API_KEY[:8]}..." if settings.AAI_API_KEY else None
        }
    }


@app.post("/api-keys")
async def update_api_keys(
    keys: ApiKeysUpdate,
    current_user: Optional[TokenData] = Depends(get_current_user)
):
    """
    Atualiza as API Keys e recarrega os modelos.
    
    Args:
        keys: Novas chaves de API
        
    Returns:
        Status da atualização e modelos recarregados
    """
    global diarization_engine, whisper_engine, assemblyai_engine
    
    try:
        logger.info("=" * 60)
        logger.info("ATUALIZANDO API KEYS E RECARREGANDO MODELOS")
        logger.info("=" * 60)
        
        updated_models = []
        errors = []
        
        # Salvar chaves no armazenamento persistente
        keys_to_save = {}
        if keys.hf_token:
            keys_to_save["HF_TOKEN"] = keys.hf_token
        if keys.aai_api_key:
            keys_to_save["AAI_API_KEY"] = keys.aai_api_key
        if keys.gemini_api_key:
            keys_to_save["GEMINI_API_KEY"] = keys.gemini_api_key
        
        if keys_to_save:
            api_keys_manager.set_multiple(keys_to_save)
            logger.info(f"✅ Chaves salvas persistentemente: {list(keys_to_save.keys())}")
        
        # Atualizar HF_TOKEN
        if keys.hf_token:
            old_hf_token = settings.HF_TOKEN
            settings.HF_TOKEN = keys.hf_token
            os.environ["HF_TOKEN"] = keys.hf_token
            
            # Recarregar Pyannote
            try:
                logger.info("🔄 Recarregando Pyannote...")
                diarization_engine = DiarizationEngine(keys.hf_token)
                updated_models.append({
                    "model": "pyannote",
                    "status": "loaded",
                    "device": diarization_engine.get_device()
                })
                logger.info(f"✅ Pyannote recarregado! Device: {diarization_engine.get_device()}")
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    error_msg = "Token inválido ou sem permissões. Verifique se o token está correto e tem permissão 'Read'."
                elif "403" in error_msg or "Forbidden" in error_msg:
                    error_msg = "Acesso negado. Você precisa aceitar os termos de uso em: https://huggingface.co/pyannote/speaker-diarization"
                logger.error(f"❌ Erro ao recarregar Pyannote: {error_msg}")
                errors.append(f"Pyannote: {error_msg}")
                diarization_engine = None
            
            # Recarregar Whisper
            try:
                logger.info("🔄 Recarregando Whisper...")
                whisper_engine = WhisperEngine(keys.hf_token)
                updated_models.append({
                    "model": "whisper",
                    "status": "loaded",
                    "device": whisper_engine.get_device()
                })
                logger.info(f"✅ Whisper recarregado! Device: {whisper_engine.get_device()}")
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    error_msg = "Token inválido ou sem permissões. Verifique se o token está correto e tem permissão 'Read'."
                elif "403" in error_msg or "Forbidden" in error_msg:
                    error_msg = "Acesso negado. Certifique-se de que o token tem permissão de leitura."
                logger.error(f"❌ Erro ao recarregar Whisper: {error_msg}")
                errors.append(f"Whisper: {error_msg}")
                whisper_engine = None
        
        # Atualizar AAI_API_KEY  
        if keys.aai_api_key:
            old_aai_key = settings.AAI_API_KEY
            settings.AAI_API_KEY = keys.aai_api_key
            os.environ["AAI_API_KEY"] = keys.aai_api_key
            
            # Recarregar AssemblyAI
            try:
                logger.info("🔄 Reconfigurando AssemblyAI...")
                assemblyai_engine = AssemblyAIEngine(keys.aai_api_key)
                updated_models.append({
                    "model": "assemblyai",
                    "status": "configured",
                    "device": assemblyai_engine.get_device()
                })
                logger.info("✅ AssemblyAI reconfigurado!")
            except Exception as e:
                logger.error(f"❌ Erro ao reconfigurar AssemblyAI: {e}")
                errors.append(f"AssemblyAI: {str(e)}")
                settings.AAI_API_KEY = old_aai_key
                if old_aai_key:
                    os.environ["AAI_API_KEY"] = old_aai_key
        
        # Atualizar GEMINI_API_KEY
        if keys.gemini_api_key:
            old_gemini_key = settings.GEMINI_API_KEY
            settings.GEMINI_API_KEY = keys.gemini_api_key
            os.environ["GEMINI_API_KEY"] = keys.gemini_api_key
            
            # Recarregar Gemini
            try:
                logger.info("🔄 Reconfigurando Gemini...")
                meeting_minutes_generator = MeetingMinutesGenerator(keys.gemini_api_key)
                updated_models.append({
                    "model": "gemini",
                    "status": "configured",
                    "device": "cloud"
                })
                logger.info("✅ Gemini reconfigurado!")
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg or "API_KEY_INVALID" in error_msg:
                    error_msg = "API Key inválida. Obtenha uma em: https://makersuite.google.com/app/apikey"
                logger.error(f"❌ Erro ao reconfigurar Gemini: {error_msg}")
                errors.append(f"Gemini: {error_msg}")
                meeting_minutes_generator = None
        
        logger.info("=" * 60)
        logger.info("ATUALIZAÇÃO CONCLUÍDA")
        logger.info("=" * 60)
        
        return {
            "success": len(errors) == 0,
            "message": "API Keys atualizadas e modelos recarregados" if len(errors) == 0 else "Algumas chaves não puderam ser atualizadas",
            "updated_models": updated_models,
            "errors": errors,
            "current_status": {
                "diarization": {
                    "loaded": diarization_engine is not None,
                    "device": diarization_engine.get_device() if diarization_engine else "not loaded"
                },
                "whisper": {
                    "loaded": whisper_engine is not None,
                    "device": whisper_engine.get_device() if whisper_engine else "not loaded"
                },
                "assemblyai": {
                    "loaded": assemblyai_engine is not None,
                    "device": assemblyai_engine.get_device() if assemblyai_engine else "not loaded"
                },
                "gemini": {
                    "loaded": meeting_minutes_generator is not None,
                    "device": "cloud" if meeting_minutes_generator else "not loaded"
                }
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Erro fatal ao atualizar API Keys: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar API Keys: {str(e)}"
        )


# ========== ENDPOINTS DIRETOS DOS SERVIÇOS (para compatibilidade) ==========

@app.post("/diarize")
async def diarize_endpoint(
    file: UploadFile = File(...),
    min_duration: float = Form(0.7),
    silence_threshold: int = Form(-30)
):
    """
    Endpoint direto de diarização (compatível com pyannote_model.py).
    
    Args:
        file: Arquivo de áudio
        min_duration: Duração mínima do segmento (segundos)
        silence_threshold: Limiar de silêncio (dB)
        
    Returns:
        Segmentos com speaker labels
    """
    if not diarization_engine:
        raise HTTPException(
            status_code=503,
            detail="Diarization engine not loaded. Check HF_TOKEN configuration."
        )
    
    temp_path = None
    temp_wav_path = None
    
    try:
        # Salvar arquivo temporário
        temp_path = f"temp/diarize_{file.filename}"
        async with aiofiles.open(temp_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        # Converter para WAV se necessário
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext != "wav":
            temp_wav_path = diarization_engine.convert_to_wav(temp_path)
        else:
            temp_wav_path = temp_path
        
        # Realizar diarização
        result = diarization_engine.diarize(temp_wav_path, min_duration, silence_threshold)
        
        return result
    
    finally:
        # Limpar arquivos temporários
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_path}: {e}")
        
        if temp_wav_path and temp_wav_path != temp_path and os.path.exists(temp_wav_path):
            try:
                os.remove(temp_wav_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_wav_path}: {e}")


@app.post("/whisper/transcribe_segment")
async def whisper_transcribe_segment_endpoint(
    file: UploadFile = File(...),
    start: float = Form(0.0),
    end: Optional[float] = Form(None)
):
    """
    Endpoint direto de transcrição Whisper (compatível com whisper_model.py).
    
    Args:
        file: Arquivo de áudio
        start: Tempo de início (segundos)
        end: Tempo de fim (segundos, None = até o final)
        
    Returns:
        Texto transcrito
    """
    if not whisper_engine:
        raise HTTPException(
            status_code=503,
            detail="Whisper engine not loaded. Check HF_TOKEN configuration."
        )
    
    temp_path = None
    
    try:
        # Salvar arquivo temporário
        temp_path = f"temp/whisper_{start}_{end}_{file.filename}"
        async with aiofiles.open(temp_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        # Transcrever segmento
        text = whisper_engine.transcribe_segment(temp_path, start, end)
        
        return {"transcription": text}
    
    finally:
        # Limpar arquivo temporário
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_path}: {e}")


@app.post("/assemblyai/transcribe_segment")
async def assemblyai_transcribe_segment_endpoint(
    file: UploadFile = File(...),
    start: float = Form(0.0),
    end: Optional[float] = Form(None)
):
    """
    Endpoint direto de transcrição AssemblyAI (compatível com assemblyai_model.py).
    
    Args:
        file: Arquivo de áudio
        start: Tempo de início (segundos)
        end: Tempo de fim (segundos, None = até o final)
        
    Returns:
        Texto transcrito
    """
    if not assemblyai_engine:
        raise HTTPException(
            status_code=503,
            detail="AssemblyAI engine not loaded. Check AAI_API_KEY configuration."
        )
    
    temp_path = None
    
    try:
        # Salvar arquivo temporário
        temp_path = f"temp/assemblyai_{start}_{end}_{file.filename}"
        async with aiofiles.open(temp_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        # Transcrever segmento
        text = assemblyai_engine.transcribe_segment(temp_path, start, end)
        
        return {"transcription": text}
    
    finally:
        # Limpar arquivo temporário
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_path}: {e}")


# ========== ENDPOINTS DE ATA DE REUNIÃO ==========

@app.post("/meeting-minutes/generate")
async def generate_meeting_minutes(
    request: MeetingMinutesRequest,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(get_current_user)
):
    """
    Gera ata de reunião a partir de uma transcrição existente.
    
    Args:
        request: Dados da requisição (transcription_id, título, data, participantes)
        
    Returns:
        Ata estruturada com resumo, to-do list, decisões, etc.
    """
    if not meeting_minutes_generator:
        raise HTTPException(
            status_code=503,
            detail="Meeting minutes generator not configured. Check GEMINI_API_KEY configuration."
        )
    
    try:
        # Buscar transcrição
        transcription = db.query(Transcription).filter(
            Transcription.id == request.transcription_id
        ).first()
        
        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        if transcription.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Transcription status is '{transcription.status}'. Only completed transcriptions can be used."
            )
        
        # Montar texto da transcrição
        segments_text = []
        for seg in transcription.segments:
            speaker = seg.get("speaker", "SPEAKER")
            text = seg.get("text", "")
            segments_text.append(f"{speaker}: {text}")
        
        full_transcription = "\n".join(segments_text)
        
        # Preparar contexto
        context = {}
        if request.title:
            context["title"] = request.title
        if request.date:
            context["date"] = request.date
        if request.participants:
            context["participants"] = request.participants
        
        # Gerar ata
        logger.info(f"Gerando ata para transcrição {request.transcription_id}...")
        minutes = meeting_minutes_generator.generate_minutes(
            transcription=full_transcription,
            meeting_context=context
        )
        
        logger.info("Ata gerada com sucesso!")
        
        return {
            "transcription_id": request.transcription_id,
            "meeting_info": {
                "title": request.title,
                "date": request.date,
                "participants": request.participants,
                "duration": transcription.duration_seconds,
                "word_count": transcription.word_count
            },
            "minutes": minutes
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating meeting minutes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/meeting-minutes/status")
async def get_meeting_minutes_status(
    current_user: Optional[TokenData] = Depends(get_current_user)
):
    """Retorna status do gerador de atas."""
    return {
        "available": meeting_minutes_generator is not None,
        "config": meeting_minutes_generator.get_config_status() if meeting_minutes_generator else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
