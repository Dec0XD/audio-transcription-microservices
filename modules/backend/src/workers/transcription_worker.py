"""
Worker de processamento de transcrição com RQ.

Consome jobs da fila Redis e executa o processamento.
Este worker roda em um processo separado.
"""

import asyncio
import logging
import time
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Transcription, TranscriptionJob
from ..utils.audio import convert_to_wav, remove_temp_file_with_retry
from ..routers.transcribe import _process_with_diarization, _process_without_diarization

logger = logging.getLogger(__name__)


def process_transcription_job_sync(transcription_id: int) -> dict:
    """
    Processa um job de transcrição de forma síncrona (chamado por RQ worker).
    
    RQ não suporta async nativamente, então usamos asyncio.run() para executar
    a lógica assíncrona.
    
    Args:
        transcription_id: ID da transcrição a processar
        
    Returns:
        Dict com status e resultado do processamento
    """
    return asyncio.run(_process_transcription_job_async(transcription_id))


async def _process_transcription_job_async(transcription_id: int) -> dict:
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
            logger.warning(f"Job ou transcrição não encontrado para id={transcription_id}")
            return {"status": "failed", "error": "Job ou transcrição não encontrado"}

        if job.status == "done":
            logger.info(f"Job {transcription_id} já foi processado")
            return {"status": "already_done"}

        start_time = time.time()
        loop = asyncio.get_running_loop()
        input_path = job.input_path

        # Atualiza status
        job.status = "processing"
        transcription.status = "processing"
        db.commit()
        logger.info(f"Processando transcrição {transcription_id}")

        # Converte para WAV
        wav_output_path = f"temp/wav_{uuid.uuid4()}.wav"
        temp_wav_path, duration = await loop.run_in_executor(
            None,
            convert_to_wav,
            input_path,
            wav_output_path,
        )

        # Processa com ou sem diarização
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

        # Calcula estatísticas
        word_count = sum(len(seg["text"].split()) for seg in segments)
        processing_time = time.time() - start_time

        # Persiste resultado
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

        logger.info(f"✅ Transcrição {transcription_id} completada em {processing_time:.2f}s")
        return {
            "status": "completed",
            "transcription_id": transcription_id,
            "processing_time": processing_time,
            "word_count": word_count,
        }

    except Exception as e:
        # Registra erro no banco
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
        
        logger.error(f"❌ Erro ao processar transcrição {transcription_id}: {e}", exc_info=True)
        return {"status": "failed", "transcription_id": transcription_id, "error": str(e)}

    finally:
        # Limpeza de arquivos temporários
        await remove_temp_file_with_retry(input_path)
        await remove_temp_file_with_retry(temp_wav_path)
        db.close()
