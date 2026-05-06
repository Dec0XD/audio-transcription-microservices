"""
Endpoints de compatibilidade com a arquitetura de microserviços anterior.

Expõe /diarize, /whisper/transcribe_segment e /assemblyai/transcribe_segment
como interfaces diretas aos engines, mantendo contrato HTTP já consumido por
clientes legados.
"""

import logging
import os
from typing import Optional

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .. import engine_registry
from ..utils.audio import remove_temp_file_with_retry

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/diarize")
async def diarize_endpoint(
    file: UploadFile = File(...),
    min_duration: float = Form(0.7),
    silence_threshold: int = Form(-30),
):
    """
    Endpoint direto de diarização (compatível com pyannote_model.py).

    Args:
        file:              Arquivo de áudio.
        min_duration:      Duração mínima do segmento (segundos).
        silence_threshold: Limiar de silêncio (dB).

    Returns:
        Segmentos com speaker labels.
    """
    if not engine_registry.diarization_engine:
        raise HTTPException(
            status_code=503,
            detail="Diarization engine not loaded. Check HF_TOKEN configuration.",
        )

    temp_path: Optional[str] = None
    temp_wav_path: Optional[str] = None

    try:
        temp_path = f"temp/diarize_{file.filename}"
        async with aiofiles.open(temp_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        file_ext = file.filename.split(".")[-1].lower()
        if file_ext != "wav":
            temp_wav_path = engine_registry.diarization_engine.convert_to_wav(temp_path)
        else:
            temp_wav_path = temp_path

        result = engine_registry.diarization_engine.diarize(
            temp_wav_path, min_duration, silence_threshold
        )
        return result

    finally:
        await remove_temp_file_with_retry(temp_path)
        if temp_wav_path and temp_wav_path != temp_path:
            await remove_temp_file_with_retry(temp_wav_path)


@router.post("/whisper/transcribe_segment")
async def whisper_transcribe_segment_endpoint(
    file: UploadFile = File(...),
    start: float = Form(0.0),
    end: Optional[float] = Form(None),
):
    """
    Endpoint direto de transcrição Whisper (compatível com whisper_model.py).

    Args:
        file:  Arquivo de áudio.
        start: Tempo de início (segundos).
        end:   Tempo de fim (segundos, None = até o final).

    Returns:
        Texto transcrito.
    """
    if not engine_registry.whisper_engine:
        raise HTTPException(
            status_code=503,
            detail="Whisper engine not loaded. Check HF_TOKEN configuration.",
        )

    temp_path: Optional[str] = None

    try:
        temp_path = f"temp/whisper_{start}_{end}_{file.filename}"
        async with aiofiles.open(temp_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        text = engine_registry.whisper_engine.transcribe_segment(temp_path, start, end)
        return {"transcription": text}

    finally:
        await remove_temp_file_with_retry(temp_path)


@router.post("/assemblyai/transcribe_segment")
async def assemblyai_transcribe_segment_endpoint(
    file: UploadFile = File(...),
    start: float = Form(0.0),
    end: Optional[float] = Form(None),
):
    """
    Endpoint direto de transcrição AssemblyAI (compatível com assemblyai_model.py).

    Args:
        file:  Arquivo de áudio.
        start: Tempo de início (segundos).
        end:   Tempo de fim (segundos, None = até o final).

    Returns:
        Texto transcrito.
    """
    if not engine_registry.assemblyai_engine:
        raise HTTPException(
            status_code=503,
            detail="AssemblyAI engine not loaded. Check AAI_API_KEY configuration.",
        )

    temp_path: Optional[str] = None

    try:
        temp_path = f"temp/assemblyai_{start}_{end}_{file.filename}"
        async with aiofiles.open(temp_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        text = engine_registry.assemblyai_engine.transcribe_segment(temp_path, start, end)
        return {"transcription": text}

    finally:
        await remove_temp_file_with_retry(temp_path)
