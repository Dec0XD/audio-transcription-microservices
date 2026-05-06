import asyncio
import logging
import os
from typing import Optional

from fastapi import HTTPException
from pydub import AudioSegment
from pydub.utils import which

logger = logging.getLogger(__name__)


def convert_to_wav(input_path: str, output_path: str) -> tuple[str, float]:
    """
    Converte arquivo de áudio para WAV.

    Args:
        input_path:  Caminho do arquivo de entrada.
        output_path: Caminho de destino do WAV (deve ser único por chamada).

    Returns:
        Tupla (caminho_wav, duração_em_segundos).
    """
    try:
        ffmpeg_path = which("ffmpeg") or which("avconv")
        ffprobe_path = which("ffprobe") or which("avprobe")
        if not ffmpeg_path or not ffprobe_path:
            raise HTTPException(
                status_code=500,
                detail=(
                    "FFmpeg/FFprobe não encontrado no sistema. "
                    "Instale o FFmpeg e adicione ao PATH para processar áudio/vídeo."
                ),
            )

        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
        duration = len(audio) / 1000.0
        return output_path, duration

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting to WAV: {e}")
        raise HTTPException(status_code=400, detail=f"Error converting audio: {str(e)}")


async def remove_temp_file_with_retry(
    path: Optional[str], attempts: int = 5, delay: float = 0.2
) -> None:
    """Remove arquivo temporário com retries para reduzir lock transitório no Windows."""
    if not path or not os.path.exists(path):
        return

    for attempt in range(1, attempts + 1):
        try:
            os.remove(path)
            return
        except PermissionError as e:
            if attempt == attempts:
                logger.warning(f"Could not remove temp file {path}: {e}")
            else:
                await asyncio.sleep(delay)
        except Exception as e:
            logger.warning(f"Could not remove temp file {path}: {e}")
            return
