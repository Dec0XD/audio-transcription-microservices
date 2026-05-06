from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import engine_registry
from ..database import get_db
from ..models import Transcription
from ..schemas import MeetingMinutesRequest
from ..security import TokenData, get_current_user

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/meeting-minutes/generate")
async def generate_meeting_minutes(
    request: MeetingMinutesRequest,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(get_current_user),
):
    """
    Gera ata de reunião a partir de uma transcrição existente.

    Args:
        request: Dados da requisição (transcription_id, título, data, participantes).

    Returns:
        Ata estruturada com resumo, to-do list, decisões, etc.
    """
    if not engine_registry.meeting_minutes_generator:
        raise HTTPException(
            status_code=503,
            detail="Meeting minutes generator not configured. Check GEMINI_API_KEY configuration.",
        )

    try:
        transcription = (
            db.query(Transcription)
            .filter(Transcription.id == request.transcription_id)
            .first()
        )

        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")

        if transcription.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Transcription status is '{transcription.status}'. Only completed transcriptions can be used.",
            )

        # Montar texto da transcrição
        segments_text = []
        for seg in transcription.segments:
            speaker = seg.get("speaker", "SPEAKER")
            text = seg.get("text", "")
            segments_text.append(f"{speaker}: {text}")

        full_transcription = "\n".join(segments_text)

        # Preparar contexto
        context: dict = {}
        if request.title:
            context["title"] = request.title
        if request.date:
            context["date"] = request.date
        if request.participants:
            context["participants"] = request.participants

        logger.info(f"Gerando ata para transcrição {request.transcription_id}...")
        minutes = engine_registry.meeting_minutes_generator.generate_minutes(
            transcription=full_transcription,
            meeting_context=context,
        )
        logger.info("Ata gerada com sucesso!")

        return {
            "transcription_id": request.transcription_id,
            "meeting_info": {
                "title": request.title,
                "date": request.date,
                "participants": request.participants,
                "duration": transcription.duration_seconds,
                "word_count": transcription.word_count,
            },
            "minutes": minutes,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating meeting minutes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meeting-minutes/status")
async def get_meeting_minutes_status(
    current_user: Optional[TokenData] = Depends(get_current_user),
):
    """Retorna status do gerador de atas."""
    return {
        "available": engine_registry.meeting_minutes_generator is not None,
        "config": (
            engine_registry.meeting_minutes_generator.get_config_status()
            if engine_registry.meeting_minutes_generator
            else None
        ),
    }
