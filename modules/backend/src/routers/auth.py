from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..config import settings
from ..security import (
    TokenData,
    create_access_token,
    get_authenticated_user,
    get_password_hash,
    require_admin,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def _is_admin_credentials_configured() -> bool:
    return bool(settings.AUTH_ADMIN_PASSWORD_HASH or settings.AUTH_ADMIN_PASSWORD)


def _validate_credentials(username: str, password: str) -> Optional[dict]:
    admin_username = settings.AUTH_ADMIN_USERNAME

    if _is_admin_credentials_configured() and username == admin_username:
        if settings.AUTH_ADMIN_PASSWORD_HASH:
            if not verify_password(password, settings.AUTH_ADMIN_PASSWORD_HASH):
                return None
        else:
            if password != settings.AUTH_ADMIN_PASSWORD:
                return None

        return {
            "sub": username,
            "roles": ["admin"],
            "scopes": [
                "manage_keys",
                "transcribe",
                "meeting_minutes",
                "read_transcriptions",
                "delete_transcriptions",
            ],
        }

    if settings.AUTH_MODE == "permissive" and settings.AUTH_ALLOW_DEMO_LOGIN:
        # Fallback controlado para migração gradual sem quebra do frontend.
        if username and password:
            return {
                "sub": username,
                "roles": ["user"],
                "scopes": ["transcribe", "meeting_minutes", "read_transcriptions"],
            }

    return None


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    principal = _validate_credentials(payload.username, payload.password)
    if not principal:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(
        data=principal,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": principal["sub"],
            "roles": principal["roles"],
            "scopes": principal["scopes"],
        },
    }


@router.get("/me")
async def me(current_user: Optional[TokenData] = Depends(get_authenticated_user)):
    if current_user is None:
        return {"authenticated": False, "user": None}

    return {
        "authenticated": True,
        "user": {
            "username": current_user.username,
            "roles": current_user.roles,
            "scopes": current_user.scopes,
        },
    }


@router.get("/config")
async def auth_config():
    return {
        "mode": settings.AUTH_MODE,
        "strict": settings.is_auth_strict,
        "demo_login": settings.AUTH_ALLOW_DEMO_LOGIN,
        "admin_configured": _is_admin_credentials_configured(),
    }


@router.get("/password-hash")
async def password_hash_for_bootstrap(
    password: str,
    current_user: Optional[TokenData] = Depends(require_admin),
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return {"hash": get_password_hash(password)}
