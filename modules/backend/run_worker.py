#!/usr/bin/env python
"""
Script para iniciar o worker de transcrição com RQ.

Uso:
    python run_worker.py

Este worker processa jobs da fila Redis de forma contínua.
Execute em um terminal separado do servidor FastAPI.
"""

import logging
import sys
from pathlib import Path

# Adiciona o diretório do backend ao path para importações
backend_src = Path(__file__).parent / "modules" / "backend" / "src"
if backend_src.exists():
    sys.path.insert(0, str(backend_src.parent))

from rq import Worker
from redis import Redis

from src.workers.config import get_redis_url, is_redis_available
from src.workers.transcription_worker import process_transcription_job_sync

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Inicia o worker RQ."""
    
    # Verifica Redis
    if not is_redis_available():
        logger.error("❌ Redis não está disponível!")
        logger.error("Instale Redis: https://redis.io/download")
        logger.error("Ou use Docker: docker run -d -p 6379:6379 redis:latest")
        sys.exit(1)
    
    logger.info("✅ Redis disponível")
    
    # Conecta ao Redis
    redis_url = get_redis_url()
    redis_conn = Redis.from_url(redis_url, decode_responses=False)
    
    logger.info(f"📦 Worker iniciado (Redis: {redis_url})")
    logger.info("👂 Aguardando jobs na fila 'transcriptions'...")
    
    # Cria e inicia worker
    worker = Worker(
        ["transcriptions"],  # Nome da fila
        connection=redis_conn,
        name="transcription-worker-1",
        job_monitoring_interval=5,
    )
    
    try:
        worker.work(with_scheduler=False, logging_level="INFO")
    except KeyboardInterrupt:
        logger.info("⏹️  Worker interrompido pelo usuário")
        sys.exit(0)


if __name__ == "__main__":
    main()
