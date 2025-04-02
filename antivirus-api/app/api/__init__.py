"""
Главный файл для инициализации всех API роутеров.
Собирает все роутеры из разных модулей в единый объект APIRouter.
"""

from fastapi import APIRouter
from .dependencies import router as dependencies_router
from .v1 import router as v1_router

# Создаем главный роутер API
api_router = APIRouter()

# Подключаем все роутеры с соответствующими префиксами
api_router.include_router(
    dependencies_router,
    prefix="/dependencies",
    tags=["dependencies"]
)

api_router.include_router(
    v1_router,
    prefix="/v1",
    tags=["v1"]
)

# Экспортируем главный роутер для использования в main.py
__all__ = ["api_router"]