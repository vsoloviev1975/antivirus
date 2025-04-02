"""
Роутер для работы с историей изменений.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, CurrentAdmin
from app.services.history import HistoryService

router = APIRouter(tags=["history"])

@router.get("/signatures/{signature_id}")
async def get_signature_history(
    signature_id: str,
    db: AsyncSession = Depends(get_db),
    admin: CurrentAdmin = Depends()
):
    """
    Получение истории изменений конкретной сигнатуры (только для админов).
    """
    service = HistoryService()
    history = await service.get_signature_history(db, signature_id)
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    return history
