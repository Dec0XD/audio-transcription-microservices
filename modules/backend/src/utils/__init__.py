"""
Utilitários para o backend de transcrição.
"""

from .gpu_utils import (
    get_device_info,
    optimize_gpu_settings,
    log_device_info,
    check_memory_requirements,
    get_optimal_whisper_dtype,
    clear_gpu_memory,
    set_memory_fraction
)

__all__ = [
    "get_device_info",
    "optimize_gpu_settings", 
    "log_device_info",
    "check_memory_requirements",
    "get_optimal_whisper_dtype",
    "clear_gpu_memory",
    "set_memory_fraction"
]