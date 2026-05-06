from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Transcription
from ..security import TokenData, get_current_user

router = APIRouter()


@router.get("/transcriptions")
async def list_transcriptions(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(get_current_user),
):
    """
    Lista transcrições com paginação opcional.

    Args:
        skip:   Registros a pular.
        limit:  Máximo de registros a retornar.
        status: Filtrar por status (processing, completed, failed).
    """
    query = db.query(Transcription)

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
    current_user: Optional[TokenData] = Depends(get_current_user),
):
    """Obtém detalhes de uma transcrição específica."""
    transcription = (
        db.query(Transcription).filter(Transcription.id == transcription_id).first()
    )

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return transcription.to_dict()


@router.delete("/transcriptions/{transcription_id}")
async def delete_transcription(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(get_current_user),
):
    """Remove uma transcrição."""
    transcription = (
        db.query(Transcription).filter(Transcription.id == transcription_id).first()
    )

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    db.delete(transcription)
    db.commit()

    return {"message": "Transcription deleted successfully"}


@router.get("/stats")
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: Optional[TokenData] = Depends(get_current_user),
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
