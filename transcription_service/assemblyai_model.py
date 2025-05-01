from fastapi import FastAPI, UploadFile, File, HTTPException
import os
from pydub import AudioSegment
from dotenv import load_dotenv
import time
import logging
import assemblyai as aai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
AAI_API_KEY = os.getenv("AAI_API_KEY")
if not AAI_API_KEY:
    raise ValueError("Chave da API AssemblyAI não fornecida. Defina AAI_API_KEY no .env.")

# Configuração do AssemblyAI
aai.settings.api_key = AAI_API_KEY
aai_config = aai.TranscriptionConfig(language_code="pt")
aai_transcriber = aai.Transcriber(config=aai_config)

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "model": "AssemblyAI",
        "device": "cloud"
    }

@app.post("/transcribe_segment")
async def transcribe_segment_assemblyai(file: UploadFile = File(...), start: float = 0.0, end: float = None):
    start_time = time.time()
    logger.info(f"Recebido pedido para transcrever segmento {start}s - {end}s com AssemblyAI")

    temp_path = "temp_audio.wav"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    audio = AudioSegment.from_file(temp_path)
    total_duration = len(audio) / 1000.0
    if end is None or end > total_duration:
        end = total_duration
    if start >= end:
        raise HTTPException(status_code=400, detail="O tempo de início deve ser menor que o tempo de fim")

    start_ms = int(start * 1000)
    end_ms = int(end * 1000)
    logger.info(f"Cortando áudio: {start_ms}ms - {end_ms}ms (duração: {end_ms - start_ms}ms)")
    
    segment_audio = audio[start_ms:end_ms]
    segment_path = "temp_segment.wav"
    segment_audio.export(segment_path, format="wav")

    segment_duration = (end_ms - start_ms) / 1000.0
    logger.info(f"Segmento exportado com duração de {segment_duration:.2f}s")

    try:
        transcript = aai_transcriber.transcribe(segment_path)
        transcription = transcript.text.strip() if transcript.text else ""
    except Exception as e:
        os.remove(temp_path)
        os.remove(segment_path)
        raise HTTPException(status_code=500, detail=f"Erro na transcrição com AssemblyAI: {str(e)}")

    os.remove(temp_path)
    os.remove(segment_path)

    end_time = time.time()
    logger.info(f"Transcrição concluída em {end_time - start_time:.2f}s: {transcription}")
    return {"transcription": transcription}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)