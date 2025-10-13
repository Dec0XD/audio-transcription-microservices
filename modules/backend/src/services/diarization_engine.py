"""
Engine de diarização usando Pyannote - carregado uma vez e reutilizado.
"""

import logging
import os
import numpy as np
import librosa
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
import torch
from pydub import AudioSegment
from ..config import settings

logger = logging.getLogger(__name__)


class DiarizationEngine:
    """Motor de diarização usando Pyannote."""
    
    def __init__(self, hf_token: str):
        self.hf_token = hf_token
        self.pipeline = None
        self._load_pipeline()
    
    def _load_pipeline(self):
        """Carrega o pipeline de diarização com configuração otimizada de GPU."""
        try:
            logger.info("Carregando pipeline de diarização Pyannote...")
            
            # Verificar disponibilidade de CUDA e configuração
            cuda_available = torch.cuda.is_available() and not settings.FORCE_CPU
            if cuda_available:
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"🎮 GPU detectada: {gpu_name} ({gpu_count} device(s))")
            else:
                if settings.FORCE_CPU:
                    logger.info("⚙️  Modo CPU forçado via configuração")
                else:
                    logger.warning("⚠️  GPU não disponível - usando CPU (será mais lento)")
            
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token
            )
            if self.pipeline is None:
                raise ValueError(
                    "Falha ao carregar pipeline. "
                    "Verifique o token e aceite os termos em "
                    "https://hf.co/pyannote/speaker-diarization-3.1"
                )
            
            # Configurar device otimizado
            if cuda_available:
                device = torch.device("cuda:0")
                logger.info("🚀 Configurando Pyannote para GPU (CUDA)...")
                
                # Configurações otimizadas para GPU
                torch.backends.cudnn.benchmark = True
                torch.backends.cudnn.deterministic = False
                
                # Limpar cache se necessário
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
            else:
                device = torch.device("cpu")
                logger.info("⚙️  Configurando Pyannote para CPU...")
                
                # Configurações otimizadas para CPU
                torch.set_num_threads(torch.get_num_threads())
            
            self.pipeline.to(device)
            self.device = device
            
            # Log detalhado
            memory_info = ""
            if cuda_available:
                memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
                memory_reserved = torch.cuda.memory_reserved(0) / 1024**3
                memory_info = f" | VRAM: {memory_allocated:.1f}GB alocada, {memory_reserved:.1f}GB reservada"
            
            logger.info(f"✅ Pipeline de diarização carregado no device: {device}{memory_info}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar pipeline de diarização: {e}")
            raise
    
    def convert_to_wav(self, input_path: str, output_path: str = "temp_converted.wav") -> str:
        """Converte arquivo de áudio para WAV."""
        try:
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format="wav")
            if not os.path.exists(output_path):
                raise ValueError(f"Falha ao criar arquivo WAV: {output_path}")
            logger.info(f"Arquivo convertido para WAV: {output_path}")
            return output_path
        except Exception as e:
            raise ValueError(f"Erro ao converter para WAV: {str(e)}")
    
    def is_valid_segment(
        self,
        audio_path: str,
        start: float,
        end: float,
        min_duration: float = 0.7,
        silence_threshold: int = -30
    ) -> bool:
        """Verifica se segmento é válido (não muito curto ou silencioso)."""
        try:
            duration = end - start
            if duration < min_duration:
                logger.warning(
                    f"Segmento muito curto: {start:.2f}s-{end:.2f}s, "
                    f"duração={duration:.2f}s"
                )
                return False
            
            audio, sr = librosa.load(audio_path, sr=None, offset=start, duration=duration)
            rms = np.sqrt(np.mean(audio**2))
            db = 20 * np.log10(rms) if rms > 0 else -np.inf
            
            if db < silence_threshold:
                logger.warning(
                    f"Segmento silencioso: {start:.2f}s-{end:.2f}s, dBFS={db:.2f}"
                )
                return False
            
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar segmento {start:.2f}s-{end:.2f}s: {e}")
            return False
    
    def diarize(self, audio_path: str, min_duration: float = 0.7, silence_threshold: int = -30) -> dict:
        """
        Realiza diarização do arquivo de áudio.
        
        Returns:
            Dict com 'segments' (lista) e 'num_speakers' (int)
        """
        if self.pipeline is None:
            raise RuntimeError("Pipeline de diarização não carregado")
        
        try:
            logger.info(f"Iniciando diarização de: {audio_path}")
            with ProgressHook() as hook:
                diarization = self.pipeline(audio_path, hook=hook)
            
            segments = []
            speakers = set()
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                if self.is_valid_segment(
                    audio_path, turn.start, turn.end, min_duration, silence_threshold
                ):
                    duration = turn.end - turn.start
                    segments.append({
                        "start": turn.start,
                        "end": turn.end,
                        "duration": duration,
                        "speaker": speaker
                    })
                    speakers.add(speaker)
                else:
                    logger.info(
                        f"Segmento ignorado: {speaker} ({turn.start:.2f}s-{turn.end:.2f}s)"
                    )
            
            if not segments:
                logger.warning("Nenhum segmento válido encontrado")
                return {"segments": [], "num_speakers": 0}
            
            logger.info(f"Diarização concluída: {len(segments)} segmentos, {len(speakers)} falantes")
            return {"segments": segments, "num_speakers": len(speakers)}
        
        except Exception as e:
            logger.error(f"Erro durante diarização: {e}")
            raise
    
    def get_device(self) -> str:
        """Retorna o device usado pelo pipeline."""
        if hasattr(self, 'device') and self.device:
            return str(self.device)
        elif self.pipeline:
            return str(self.pipeline.device)
        return "not loaded"
