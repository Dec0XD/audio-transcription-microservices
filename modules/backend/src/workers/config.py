"""Configuração centralizada do Redis para fila de jobs."""

import os
from typing import Optional


def get_redis_url() -> str:
    """Obtém URL do Redis da variável de ambiente ou usa local."""
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def is_redis_available() -> bool:
    """Verifica se Redis está disponível."""
    try:
        import redis
        r = redis.Redis.from_url(get_redis_url(), decode_responses=False)
        r.ping()
        return True
    except Exception as e:
        print(f"⚠️  Redis não disponível: {e}")
        return False
