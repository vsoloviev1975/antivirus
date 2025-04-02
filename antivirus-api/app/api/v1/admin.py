"""
Административные эндпоинты.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from app.api.dependencies import get_db, CurrentAdmin
from app.services.admin import AdminService

router = APIRouter(tags=["admin"], prefix="/admin")

@router.get("/audit")
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    admin: CurrentAdmin = Depends(),
    limit: int = 100,
    offset: int = 0
):
    """
    Получение аудит-лога (только для админов).
    """
    service = AdminService()
    return await service.get_audit_logs(db, limit, offset)

@router.get("/stats")
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    admin: CurrentAdmin = Depends()
):
    """
    Получение системной статистики (только для админов).
    """
    service = AdminService()
    return await service.get_system_stats(db)
