"""
Роутер для сканирования файлов.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, CurrentUser
from app.services.scan import ScanService

router = APIRouter(tags=["scan"])

@router.post("/quick/{file_id}")
async def quick_scan(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends()
):
    """
    Быстрое сканирование файла.
    """
    service = ScanService()
    return await service.quick_scan(db, file_id, current_user.id)

@router.post("/deep/{file_id}")
async def deep_scan(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends()
):
    """
    Глубокий анализ файла.
    """
    service = ScanService()
    return await service.deep_scan(db, file_id, current_user.id)
