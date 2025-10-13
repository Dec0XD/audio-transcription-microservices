"""
Serviço de diarização de áudio.
"""

import logging
from typing import Dict, List, Optional
import httpx
from ..config import settings

logger = logging.getLogger(__name__)


class DiarizationService:
    """Serviço para realizar diarização de áudio (identificação de falantes)."""
    
    def __init__(self):
        self.service_url = settings.DIARIZATION_SERVICE_URL
        self.timeout = httpx.Timeout(600.0, connect=10.0)
    
    async def check_health(self) -> bool:
        """Verifica se o serviço de diarização está disponível."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{self.service_url}/health")
                response.raise_for_status()
                return True
        except Exception as e:
            logger.warning(f"Diarization service health check failed: {e}")
            return False
    
    async def diarize(self, audio_file_path: str) -> Dict:
        """
        Realiza diarização do arquivo de áudio.
        
        Args:
            audio_file_path: Caminho para o arquivo de áudio
            
        Returns:
            Dict contendo segmentos e número de falantes
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                with open(audio_file_path, "rb") as f:
                    files = {"file": f}
                    response = await client.post(
                        f"{self.service_url}/diarize",
                        files=files
                    )
                    response.raise_for_status()
                    return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during diarization: {e}")
            raise Exception(f"Diarization service error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error during diarization: {e}")
            raise Exception(f"Diarization failed: {str(e)}")
    
    def merge_segments(
        self,
        diarization_segments: List[Dict],
        max_gap: float = 1.0
    ) -> List[Dict]:
        """
        Mescla segmentos consecutivos do mesmo falante.
        
        Args:
            diarization_segments: Lista de segmentos de diarização
            max_gap: Intervalo máximo entre segmentos para mesclar (em segundos)
            
        Returns:
            Lista de segmentos mesclados
        """
        if not diarization_segments:
            return []
        
        merged = []
        current = diarization_segments[0].copy()
        
        for segment in diarization_segments[1:]:
            # Se é o mesmo falante e o gap é pequeno, mesclar
            if (segment["speaker"] == current["speaker"] and
                segment["start"] - current["end"] <= max_gap):
                current["end"] = segment["end"]
                current["duration"] = current["end"] - current["start"]
            else:
                # Caso contrário, adicionar o segmento atual e iniciar um novo
                merged.append(current)
                current = segment.copy()
        
        # Adicionar o último segmento
        merged.append(current)
        
        return merged
