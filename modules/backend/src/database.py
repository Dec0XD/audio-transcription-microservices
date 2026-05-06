import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings
from .models import Base

# ---------------------------------------------------------------------------
# Engine e session factory
# ---------------------------------------------------------------------------
_connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar tabelas e diretórios na importação do módulo (igual ao comportamento
# original em main.py – garante que o schema exista antes do primeiro request).
Base.metadata.create_all(bind=engine)
os.makedirs("database", exist_ok=True)
os.makedirs("temp", exist_ok=True)


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
