from fastapi import FastAPI, UploadFile, File
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
import torch
import os
from pydub import AudioSegment
from dotenv import load_dotenv
import logging
import numpy as np
import librosa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise ValueError("Token Hugging Face não fornecido. Defina a variável HF_TOKEN no arquivo .env.")

app = FastAPI()

# Carregar pipeline de diarização com autenticação
try:
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=HF_TOKEN
    )
    if pipeline is None:
        raise ValueError("Falha ao carregar o pipeline. Verifique o token e os termos de uso em https://hf.co/pyannote/speaker-diarization-3.1")
    pipeline.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
except Exception as e:
    logger.error(f"Erro ao carregar o pipeline: {str(e)}")
    raise

def convert_to_wav(input_path, output_path="converted_audio.wav"):
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
        if not os.path.exists(output_path):
            raise ValueError(f"Falha ao criar arquivo WAV: {output_path} não encontrado.")
        logger.info(f"Arquivo WAV criado com sucesso: {output_path}")
        return output_path
    except Exception as e:
        raise ValueError(f"Erro ao converter arquivo de áudio para WAV: {str(e)}")

def is_valid_segment(audio_path, start, end, min_duration=0.7, silence_threshold=-30):
    """Verifica se o segmento de áudio é válido (não é muito curto ou silencioso)."""
    try:
        duration = end - start
        if duration < min_duration:
            logger.warning(f"Segmento muito curto: {start:.2f}s - {end:.2f}s, duração={duration:.2f}s")
            return False
        audio, sr = librosa.load(audio_path, sr=None, offset=start, duration=duration)
        # Verificar nível de energia (dBFS)
        rms = np.sqrt(np.mean(audio**2))
        db = 20 * np.log10(rms) if rms > 0 else -np.inf
        if db < silence_threshold:
            logger.warning(f"Segmento silencioso: {start:.2f}s - {end:.2f}s, dBFS={db:.2f}")
            return False
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar segmento {start:.2f}s - {end:.2f}s: {str(e)}")
        return False

@app.get("/health")
async def health_check():
    return {"status": "ok", "model": "pyannote/speaker-diarization-3.1", "device": str(pipeline.device)}

@app.post("/diarize")
async def diarize_audio(file: UploadFile = File(...)):
    # Salvar arquivo temporário
    temp_input_path = f"temp_{file.filename}"
    with open(temp_input_path, "wb") as f:
        f.write(file.file.read())

    # Converter para WAV
    temp_wav_path = "temp_audio.wav"
    try:
        convert_to_wav(temp_input_path, temp_wav_path)
    except ValueError as e:
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        raise

    # Realizar diarização com ProgressHook
    try:
        with ProgressHook() as hook:
            diarization = pipeline(temp_wav_path, hook=hook)

        segments = []
        speakers = set()
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            # Verificar se o segmento é válido
            if is_valid_segment(temp_wav_path, turn.start, turn.end):
                duration = turn.end - turn.start
                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "duration": duration,
                    "speaker": speaker
                })
                speakers.add(speaker)
            else:
                logger.info(f"Segmento ignorado: {speaker} ({turn.start:.2f}s - {turn.end:.2f}s)")

        if not segments:
            logger.warning("Nenhum segmento válido encontrado. Retornando resultado vazio.")
            result = {
                "segments": [],
                "num_speakers": 0
            }
        else:
            result = {
                "segments": segments,
                "num_speakers": len(speakers)
            }
    finally:
        # Limpar arquivos temporários
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)