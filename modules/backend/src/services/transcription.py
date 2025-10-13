"""
Serviço de transcrição de áudio.
"""

import logging
from typing import Dict, Literal
import httpx
from ..config import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Serviço para realizar transcrição de áudio."""
    
    def __init__(self):
        self.whisper_url = settings.WHISPER_SERVICE_URL
        self.assemblyai_url = settings.ASSEMBLYAI_SERVICE_URL
        self.timeout = httpx.Timeout(600.0, connect=10.0)
    
    async def check_health(
        self,
        model: Literal["whisper", "assemblyai"] = "whisper"
    ) -> bool:
        """Verifica se o serviço de transcrição está disponível."""
        try:
            url = self.whisper_url if model == "whisper" else self.assemblyai_url
            
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{url}/health")
                response.raise_for_status()
                return True
        
        except Exception as e:
            logger.warning(f"{model} service health check failed: {e}")
            return False
    
    async def transcribe_segment(
        self,
        audio_file_path: str,
        start: float = 0.0,
        end: float = None,
        model: Literal["whisper", "assemblyai"] = "whisper"
    ) -> str:
        """
        Transcreve um segmento de áudio.
        
        Args:
            audio_file_path: Caminho para o arquivo de áudio
            start: Tempo de início do segmento (segundos)
            end: Tempo de fim do segmento (segundos, None = até o final)
            model: Modelo a usar ("whisper" ou "assemblyai")
            
        Returns:
            Texto transcrito
        """
        try:
            url = self.whisper_url if model == "whisper" else self.assemblyai_url
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                with open(audio_file_path, "rb") as f:
                    files = {"file": f}
                    data = {"start": start}
                    if end is not None:
                        data["end"] = end
                    
                    response = await client.post(
                        f"{url}/transcribe_segment",
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    result = response.json()
                    return result.get("transcription", "")
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during transcription: {e}")
            raise Exception(f"Transcription service error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise Exception(f"Transcription failed: {str(e)}")
    
    async def get_available_model(self) -> str:
        """
        Retorna o primeiro modelo disponível.
        
        Returns:
            Nome do modelo disponível ("whisper" ou "assemblyai")
        """
        # Tentar Whisper primeiro (local, mais rápido)
        if await self.check_health("whisper"):
            return "whisper"
        
        # Tentar AssemblyAI (cloud, mais preciso)
        if await self.check_health("assemblyai"):
            return "assemblyai"
        
        raise Exception("No transcription service available")
