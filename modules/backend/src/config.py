"""
Configurações da aplicação usando Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # API Keys
    HF_TOKEN: Optional[str] = Field(default=None, description="Hugging Face API Token")
    AAI_API_KEY: Optional[str] = Field(default=None, description="AssemblyAI API Key")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./database/transcriptions.db",
        description="Database connection URL"
    )
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", description="API Host")
    API_PORT: int = Field(default=2020, description="API Port")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-this-in-production",
        description="Secret key for JWT"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT Algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time"
    )
    
    # Services URLs
    DIARIZATION_SERVICE_URL: str = Field(
        default="http://localhost:8001",
        description="Diarization service URL"
    )
    WHISPER_SERVICE_URL: str = Field(
        default="http://localhost:8000",
        description="Whisper service URL"
    )
    ASSEMBLYAI_SERVICE_URL: str = Field(
        default="http://localhost:8002",
        description="AssemblyAI service URL"
    )
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = Field(
        default=500,
        description="Maximum upload size in MB"
    )
    ALLOWED_EXTENSIONS: str = Field(
        default="mp3,wav,mp4,mpeg,m4a,flac",
        description="Allowed file extensions"
    )
    
    # Processing
    DEFAULT_TRANSCRIPTION_MODEL: str = Field(
        default="whisper",
        description="Default transcription model (whisper or assemblyai)"
    )
    MIN_SEGMENT_DURATION: float = Field(
        default=0.7,
        description="Minimum segment duration in seconds"
    )
    SILENCE_THRESHOLD: int = Field(
        default=-30,
        description="Silence threshold in dB"
    )
    
    # GPU/Device Configuration
    FORCE_CPU: bool = Field(
        default=False,
        description="Force CPU usage even if GPU is available"
    )
    GPU_MEMORY_FRACTION: float = Field(
        default=0.8,
        description="Fraction of GPU memory to use (0.1-1.0)"
    )
    WHISPER_DTYPE: str = Field(
        default="auto",
        description="Whisper model dtype (auto, float16, float32)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def allowed_extensions_list(self) -> list[str]:
        """Retorna lista de extensões permitidas."""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def max_upload_size_bytes(self) -> int:
        """Retorna tamanho máximo de upload em bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# Instância global de configurações
settings = Settings()
