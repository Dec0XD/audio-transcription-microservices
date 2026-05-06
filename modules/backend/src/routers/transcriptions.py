from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..authorization import enforce_transcription_access, is_admin
from ..database import get_db
from ..models import Transcription, TranscriptionOwnership
from ..config import settings
from ..security import TokenData, require_scope_when

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
