from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

from .config import settings


# Configuração de criptografia de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


class Token(BaseModel):
    """Modelo de token JWT."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Dados extraídos do token."""
    username: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera hash da senha."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria token de acesso JWT."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decodifica token de acesso JWT."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        
        if username is None:
            return None
        
        return TokenData(
            username=username,
            roles=payload.get("roles", []),
            scopes=payload.get("scopes", []),
        )
    
    except JWTError:
        return None


async def get_optional_user(token: str = Depends(oauth2_scheme)) -> Optional[TokenData]:
    """
    Obtém o usuário atual a partir do token.
    Retorna None se não houver token (permite acesso anônimo).
    """
    if token is None:
        return None
    
    token_data = decode_access_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


async def get_authenticated_user(
    current_user: Optional[TokenData] = Depends(get_optional_user),
) -> Optional[TokenData]:
    """
    Usuário autenticado obrigatório em modo strict.
    Em modo permissive, mantém compatibilidade e permite acesso sem token.
    """
    if current_user is None and settings.is_auth_strict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_authentication(current_user: Optional[TokenData] = Depends(get_authenticated_user)):
    """
    Dependência que requer autenticação.
    Use em rotas que precisam de usuário autenticado.
    """
    if current_user is None and settings.is_auth_strict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return current_user


def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[TokenData]:
    """Alias de compatibilidade para chamadas antigas."""
    if token is None:
        return None
    token_data = decode_access_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


def require_scope(scope: str):
    def _require_scope(
        current_user: Optional[TokenData] = Depends(get_authenticated_user),
    ) -> Optional[TokenData]:
        if current_user is None:
            return None

        if "admin" in current_user.roles:
            return current_user

        if scope not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}",
            )
        return current_user

    return _require_scope


def require_scope_when(scope: str, enabled: bool):
    def _require_scope_when(
        current_user: Optional[TokenData] = Depends(get_optional_user),
    ) -> Optional[TokenData]:
        if not enabled:
            return current_user

        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if "admin" in current_user.roles:
            return current_user

        if scope not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}",
            )

        return current_user

    return _require_scope_when


def require_admin(
    current_user: Optional[TokenData] = Depends(get_authenticated_user),
) -> Optional[TokenData]:
    if current_user is None:
        return None

    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user


def require_admin_when(enabled: bool):
    def _require_admin_when(
        current_user: Optional[TokenData] = Depends(get_optional_user),
    ) -> Optional[TokenData]:
        if not enabled:
            return current_user

        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required",
            )

        return current_user

    return _require_admin_when
