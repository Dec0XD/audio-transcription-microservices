import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings
from .models import Base


def _resolve_database_url(db_url: str) -> str:
    """Resolve SQLite URL relativa para um caminho absoluto no backend."""
    if not db_url.startswith("sqlite"):
        return db_url

    backend_root = Path(__file__).resolve().parents[1]

    if db_url.startswith("sqlite:///./"):
        relative_path = db_url.replace("sqlite:///./", "", 1)
        absolute_path = (backend_root / relative_path).resolve()
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{absolute_path.as_posix()}"

    # Mantem URLs SQLite absolutas inalteradas.
    return db_url

# ---------------------------------------------------------------------------
# Engine e session factory
# ---------------------------------------------------------------------------
resolved_database_url = _resolve_database_url(settings.DATABASE_URL)
_connect_args = {"check_same_thread": False} if "sqlite" in resolved_database_url else {}

engine = create_engine(resolved_database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

backend_root = Path(__file__).resolve().parents[1]
(backend_root / "database").mkdir(parents=True, exist_ok=True)
(backend_root / "temp").mkdir(parents=True, exist_ok=True)

# Criar tabelas e diretórios na importação do módulo (igual ao comportamento
# original em main.py – garante que o schema exista antes do primeiro request).
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db():
    """Dependency que fornece uma sessão SQLAlchemy por request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
