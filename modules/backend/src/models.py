"""
Modelos de dados usando SQLAlchemy.
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Transcription(Base):
    """Modelo para armazenar transcrições."""
    
    __tablename__ = "transcriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_mb = Column(Float, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    
    # Modelo e configurações usadas
    transcription_model = Column(String(50), nullable=False)
    use_diarization = Column(Boolean, default=False)
    
    # Resultados
    segments = Column(JSON, nullable=False)  # Lista de segmentos transcritos
    num_speakers = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    
    # Metadados
    processing_time_seconds = Column(Float, nullable=True)
    status = Column(String(20), default="processing")  # processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Transcription(id={self.id}, filename={self.filename}, status={self.status})>"
    
    def to_dict(self):
        """Converte o modelo para dicionário."""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size_mb": self.file_size_mb,
            "duration_seconds": self.duration_seconds,
            "transcription_model": self.transcription_model,
            "use_diarization": self.use_diarization,
            "segments": self.segments,
            "num_speakers": self.num_speakers,
            "word_count": self.word_count,
            "processing_time_seconds": self.processing_time_seconds,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class User(Base):
    """Modelo para usuários (opcional - para autenticação futura)."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
