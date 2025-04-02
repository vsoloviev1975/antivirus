"""
Роутер для генерации отчетов.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, CurrentAdmin
from app.services.reports import ReportService

router = APIRouter(tags=["reports"])

@router.get("/scan-stats")
async def generate_scan_report(
    db: AsyncSession = Depends(get_db),
    admin: CurrentAdmin = Depends()
):
    """
    Генерация отчета по сканированиям (только для админов).
    """
    service = ReportService()
    return await service.generate_scan_report(db)
