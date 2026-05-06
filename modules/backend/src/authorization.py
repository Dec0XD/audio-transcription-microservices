from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .config import settings
from .models import TranscriptionOwnership
from .security import TokenData


def is_admin(user: Optional[TokenData]) -> bool:
    return bool(user and "admin" in user.roles)


def enforce_transcription_access(
    db: Session,
    transcription_id: int,
    current_user: Optional[TokenData],
    write: bool = False,
):
    """
    Enforce owner-based authorization for a transcription.

    Compat behavior:
    - permissive mode: legacy rows without owner remain accessible
    - strict mode: legacy rows without owner are denied for non-admin users
    """
    if not current_user or is_admin(current_user):
        return

    owner = (
        db.query(TranscriptionOwnership)
        .filter(TranscriptionOwnership.transcription_id == transcription_id)
        .first()
    )

    if owner is None:
        if settings.is_auth_strict:
            raise HTTPException(
                status_code=403,
                detail="Legacy transcription without owner is not accessible in strict mode",
            )
        return

    if owner.owner_sub != current_user.username:
        raise HTTPException(status_code=403, detail="You do not have access to this transcription")


def create_transcription_owner(
    db: Session,
    transcription_id: int,
    current_user: Optional[TokenData],
):
    """Persiste owner de novas transcrições quando usuário autenticado existir."""
    if not current_user or not current_user.username:
        return

    owner = TranscriptionOwnership(
        transcription_id=transcription_id,
        owner_sub=current_user.username,
    )
    db.add(owner)
    db.commit()
