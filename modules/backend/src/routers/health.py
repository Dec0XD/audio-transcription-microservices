from fastapi import APIRouter

from .. import engine_registry

router = APIRouter()


@router.get("/")
async def root():
    """Endpoint raiz."""
    return {
        "message": "Transcription API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@router.get("/health")
async def health_check():
    """Verifica a saúde da API e o estado de todos os engines carregados."""
    return {
        "status": "ok",
        "models": {
            "diarization": {
                "loaded": engine_registry.diarization_engine is not None,
                "device": (
                    engine_registry.diarization_engine.get_device()
                    if engine_registry.diarization_engine
                    else "not loaded"
                ),
            },
            "whisper": {
                "loaded": engine_registry.whisper_engine is not None,
                "device": (
                    engine_registry.whisper_engine.get_device()
                    if engine_registry.whisper_engine
                    else "not loaded"
                ),
            },
            "assemblyai": {
                "loaded": engine_registry.assemblyai_engine is not None,
                "device": (
                    engine_registry.assemblyai_engine.get_device()
                    if engine_registry.assemblyai_engine
                    else "not loaded"
                ),
            },
        },
        "database": "connected",
    }
