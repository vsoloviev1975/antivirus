"""
Инициализация API v1. Подключение всех роутеров версии 1.
"""

from fastapi import APIRouter
from .users import router as users_router
from .files import router as files_router
from .signatures import router as signatures_router
from .admin import router as admin_router
from .system import router as system_router
from .history import router as history_router
from .reports import router as reports_router
from .scan import router as scan_router

router = APIRouter(prefix="/v1")

# Обязательные роутеры
router.include_router(users_router)
router.include_router(files_router)
router.include_router(signatures_router)
router.include_router(admin_router)
router.include_router(system_router)

# Опциональные роутеры
router.include_router(history_router)
router.include_router(reports_router)
router.include_router(scan_router)

__all__ = ["router"]
