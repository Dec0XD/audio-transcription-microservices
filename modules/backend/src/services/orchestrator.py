"""
Orquestrador de serviços de transcrição e diarização.
"""

import logging
import asyncio
from typing import Dict, List, Optional
from pydub import AudioSegment
import os

from .diarization import DiarizationService
from .transcription import TranscriptionService
from ..config import settings

logger = logging.getLogger(__name__)


class TranscriptionOrchestrator:
    """Orquestra o processo completo de transcrição e diarização."""
    
    def __init__(self):
        self.diarization_service = DiarizationService()
        self.transcription_service = TranscriptionService()
    
    async def process_audio(
        self,
        audio_file_path: str,
        use_diarization: bool = False,
        transcription_model: Optional[str] = None
    ) -> Dict:
        """
        Processa um arquivo de áudio completo.
        
        Args:
            audio_file_path: Caminho para o arquivo de áudio
            use_diarization: Se deve usar diarização de falantes
            transcription_model: Modelo de transcrição ("whisper" ou "assemblyai")
            
        Returns:
            Dict com segmentos transcritos e metadados
        """
        # Verificar modelo disponível
        if transcription_model is None:
            transcription_model = await self.transcription_service.get_available_model()
        
        logger.info(f"Processing audio with model: {transcription_model}, diarization: {use_diarization}")
        
        # Obter duração do áudio
        audio = AudioSegment.from_file(audio_file_path)
        total_duration = len(audio) / 1000.0
        
        segments = []
        
        if use_diarization:
            # Realizar diarização
            diarization_available = await self.diarization_service.check_health()
            
            if not diarization_available:
                logger.warning("Diarization service not available, processing without diarization")
                use_diarization = False
        
        if use_diarization:
            # Processar com diarização
            segments = await self._process_with_diarization(
                audio_file_path,
                transcription_model
            )
        else:
            # Processar sem diarização (arquivo completo)
            segments = await self._process_without_diarization(
                audio_file_path,
                total_duration,
                transcription_model
            )
        
        # Calcular estatísticas
        num_speakers = len(set(seg.get("speaker", "SPEAKER_00") for seg in segments))
        word_count = sum(len(seg.get("text", "").split()) for seg in segments)
        
        return {
            "segments": segments,
            "num_speakers": num_speakers if use_diarization else None,
            "word_count": word_count,
            "duration": total_duration,
            "model": transcription_model,
            "diarization": use_diarization
        }
    
    async def _process_with_diarization(
        self,
        audio_file_path: str,
        transcription_model: str
    ) -> List[Dict]:
        """Processa áudio com diarização."""
        logger.info("Performing diarization...")
        
        # Realizar diarização
        diarization_result = await self.diarization_service.diarize(audio_file_path)
        diarization_segments = diarization_result.get("segments", [])
        
        if not diarization_segments:
            logger.warning("No diarization segments found")
            return []
        
        # Mesclar segmentos consecutivos do mesmo falante
        merged_segments = self.diarization_service.merge_segments(diarization_segments)
        
        logger.info(f"Processing {len(merged_segments)} segments...")
        
        # Transcrever cada segmento em paralelo
        transcription_tasks = []
        for segment in merged_segments:
            task = self.transcription_service.transcribe_segment(
                audio_file_path,
                start=segment["start"],
                end=segment["end"],
                model=transcription_model
            )
            transcription_tasks.append(task)
        
        # Aguardar todas as transcrições
        transcriptions = await asyncio.gather(*transcription_tasks, return_exceptions=True)
        
        # Combinar resultados
        result_segments = []
        for segment, transcription in zip(merged_segments, transcriptions):
            if isinstance(transcription, Exception):
                logger.error(f"Transcription failed for segment: {segment}")
                transcription = ""
            
            result_segments.append({
                "speaker": segment["speaker"],
                "start": segment["start"],
                "end": segment["end"],
                "text": transcription.strip()
            })
        
        return result_segments
    
    async def _process_without_diarization(
        self,
        audio_file_path: str,
        duration: float,
        transcription_model: str
    ) -> List[Dict]:
        """Processa áudio sem diarização."""
        logger.info("Processing without diarization...")
        
        # Transcrever arquivo completo
        transcription = await self.transcription_service.transcribe_segment(
            audio_file_path,
            start=0.0,
            end=None,
            model=transcription_model
        )
        
        return [{
            "speaker": "SPEAKER_00",
            "start": 0.0,
            "end": duration,
            "text": transcription.strip()
        }]
    
    async def check_services_health(self) -> Dict[str, bool]:
        """Verifica a saúde de todos os serviços."""
        return {
            "diarization": await self.diarization_service.check_health(),
            "whisper": await self.transcription_service.check_health("whisper"),
            "assemblyai": await self.transcription_service.check_health("assemblyai"),
        }
