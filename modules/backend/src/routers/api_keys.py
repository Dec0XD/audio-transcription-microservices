"""
Router de gerenciamento de API Keys.

Toda mutação dos engines usa `engine_registry.mutation_lock` para garantir
que um reload não interfira em uma transcrição em andamento (e vice-versa).
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from .. import engine_registry
from ..api_keys_manager import api_keys_manager
from ..config import settings
from ..schemas import ApiKeysUpdate
from ..security import TokenData, get_current_user
from ..services.diarization_engine import DiarizationEngine
from ..services.meeting_minutes import MeetingMinutesGenerator
from ..services.transcription_engine import AssemblyAIEngine, WhisperEngine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api-keys")
async def get_api_keys_status(
    current_user: Optional[TokenData] = Depends(get_current_user),
):
    """Retorna o status das API Keys sem expor os valores completos."""
    return {
        "hf_token": {
            "configured": bool(settings.HF_TOKEN),
            "value": f"{settings.HF_TOKEN[:8]}..." if settings.HF_TOKEN else None,
        },
        "aai_api_key": {
            "configured": bool(settings.AAI_API_KEY),
            "value": f"{settings.AAI_API_KEY[:8]}..." if settings.AAI_API_KEY else None,
        },
    }


@router.post("/api-keys")
async def update_api_keys(
    keys: ApiKeysUpdate,
    current_user: Optional[TokenData] = Depends(get_current_user),
):
    """
    Atualiza as API Keys e recarrega os engines afetados.

    O reload é protegido por `engine_registry.mutation_lock` para evitar
    condição de corrida com requests de transcrição em andamento.
    """
    try:
        logger.info("=" * 60)
        logger.info("ATUALIZANDO API KEYS E RECARREGANDO ENGINES")
        logger.info("=" * 60)

        updated_models: list = []
        errors: list = []

        # Persistir chaves antes de tentar carregar os engines
        keys_to_save: dict = {}
        if keys.hf_token:
            keys_to_save["HF_TOKEN"] = keys.hf_token
        if keys.aai_api_key:
            keys_to_save["AAI_API_KEY"] = keys.aai_api_key
        if keys.gemini_api_key:
            keys_to_save["GEMINI_API_KEY"] = keys.gemini_api_key

        if keys_to_save:
            api_keys_manager.set_multiple(keys_to_save)
            logger.info(f"✅ Chaves salvas persistentemente: {list(keys_to_save.keys())}")

        # Adquirir lock antes de qualquer reatribuição de engine
        async with engine_registry.mutation_lock:
            # ---- HF_TOKEN → Pyannote + Whisper ----
            if keys.hf_token:
                settings.HF_TOKEN = keys.hf_token
                os.environ["HF_TOKEN"] = keys.hf_token

                try:
                    logger.info("🔄 Recarregando Pyannote...")
                    engine_registry.diarization_engine = DiarizationEngine(keys.hf_token)
                    updated_models.append({
                        "model": "pyannote",
                        "status": "loaded",
                        "device": engine_registry.diarization_engine.get_device(),
                    })
                    logger.info(f"✅ Pyannote recarregado! Device: {engine_registry.diarization_engine.get_device()}")
                except Exception as e:
                    error_msg = _humanize_hf_error(str(e), "pyannote")
                    logger.error(f"❌ Erro ao recarregar Pyannote: {error_msg}")
                    errors.append(f"Pyannote: {error_msg}")
                    engine_registry.diarization_engine = None

                try:
                    logger.info("🔄 Recarregando Whisper...")
                    engine_registry.whisper_engine = WhisperEngine(keys.hf_token)
                    updated_models.append({
                        "model": "whisper",
                        "status": "loaded",
                        "device": engine_registry.whisper_engine.get_device(),
                    })
                    logger.info(f"✅ Whisper recarregado! Device: {engine_registry.whisper_engine.get_device()}")
                except Exception as e:
                    error_msg = _humanize_hf_error(str(e), "whisper")
                    logger.error(f"❌ Erro ao recarregar Whisper: {error_msg}")
                    errors.append(f"Whisper: {error_msg}")
                    engine_registry.whisper_engine = None

            # ---- AAI_API_KEY → AssemblyAI ----
            if keys.aai_api_key:
                old_aai_key = settings.AAI_API_KEY
                settings.AAI_API_KEY = keys.aai_api_key
                os.environ["AAI_API_KEY"] = keys.aai_api_key

                try:
                    logger.info("🔄 Reconfigurando AssemblyAI...")
                    engine_registry.assemblyai_engine = AssemblyAIEngine(keys.aai_api_key)
                    updated_models.append({
                        "model": "assemblyai",
                        "status": "configured",
                        "device": engine_registry.assemblyai_engine.get_device(),
                    })
                    logger.info("✅ AssemblyAI reconfigurado!")
                except Exception as e:
                    logger.error(f"❌ Erro ao reconfigurar AssemblyAI: {e}")
                    errors.append(f"AssemblyAI: {str(e)}")
                    # Reverter chave em settings/env se o engine falhou
                    settings.AAI_API_KEY = old_aai_key
                    if old_aai_key:
                        os.environ["AAI_API_KEY"] = old_aai_key

            # ---- GEMINI_API_KEY → MeetingMinutesGenerator ----
            if keys.gemini_api_key:
                settings.GEMINI_API_KEY = keys.gemini_api_key
                os.environ["GEMINI_API_KEY"] = keys.gemini_api_key

                try:
                    logger.info("🔄 Reconfigurando Gemini...")
                    engine_registry.meeting_minutes_generator = MeetingMinutesGenerator(
                        keys.gemini_api_key
                    )
                    updated_models.append({
                        "model": "gemini",
                        "status": "configured",
                        "device": "cloud",
                    })
                    logger.info("✅ Gemini reconfigurado!")
                except Exception as e:
                    error_msg = _humanize_gemini_error(str(e))
                    logger.error(f"❌ Erro ao reconfigurar Gemini: {error_msg}")
                    errors.append(f"Gemini: {error_msg}")
                    engine_registry.meeting_minutes_generator = None

        logger.info("=" * 60)
        logger.info("ATUALIZAÇÃO CONCLUÍDA")
        logger.info("=" * 60)

        return {
            "success": len(errors) == 0,
            "message": (
                "API Keys atualizadas e modelos recarregados"
                if not errors
                else "Algumas chaves não puderam ser atualizadas"
            ),
            "updated_models": updated_models,
            "errors": errors,
            "current_status": _build_status_snapshot(),
        }

    except Exception as e:
        logger.error(f"❌ Erro fatal ao atualizar API Keys: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar API Keys: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _build_status_snapshot() -> dict:
    return {
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
        "gemini": {
            "loaded": engine_registry.meeting_minutes_generator is not None,
            "device": "cloud" if engine_registry.meeting_minutes_generator else "not loaded",
        },
    }


def _humanize_hf_error(msg: str, model: str) -> str:
    if "401" in msg or "Unauthorized" in msg:
        return "Token inválido ou sem permissões. Verifique se o token está correto e tem permissão 'Read'."
    if "403" in msg or "Forbidden" in msg:
        return (
            f"Acesso negado ao {model}. Você precisa aceitar os termos de uso no Hugging Face."
        )
    return msg


def _humanize_gemini_error(msg: str) -> str:
    if "401" in msg or "Unauthorized" in msg or "API_KEY_INVALID" in msg:
        return "API Key inválida. Obtenha uma em: https://makersuite.google.com/app/apikey"
    return msg
