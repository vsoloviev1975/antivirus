"""
Системные эндпоинты.
"""
from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter(tags=["system"])

@router.get("/health")
async def health_check():
    """
    Проверка здоровья сервиса.
    Возвращает текущее время и статус работы.
    """
    return {
        "status": "OK",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/metrics")
async def system_metrics():
    """
    Получение системных метрик.
    """
    return {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "process_memory": psutil.Process(os.getpid()).memory_info().rss
    }
