"""
Роутер для работы с антивирусными сигнатурами.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.signature import (
    SignatureInDB,
    SignatureCreate,
    SignatureUpdate,
    SignatureDiffQuery
)
from app.api.dependencies import get_db, CurrentAdmin
from app.services.signature import SignatureService

router = APIRouter(tags=["signatures"])

@router.get("/", response_model=list[SignatureInDB])
async def list_signatures(
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка всех актуальных сигнатур.
    """
    service = SignatureService()
    return await service.get_all_signatures(db)

@router.post("/", response_model=SignatureInDB, status_code=201)
async def create_signature(
    signature: SignatureCreate,
    db: AsyncSession = Depends(get_db),
    admin: CurrentAdmin = Depends()
):
    """
    Создание новой сигнатуры (только для админов).
    """
    service = SignatureService()
    return await service.create_signature(db, signature, admin)

@router.get("/diff", response_model=list[SignatureInDB])
async def get_signatures_diff(
    query: SignatureDiffQuery,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение изменений сигнатур с указанной даты.
    """
    service = SignatureService()
    return await service.get_signatures_diff(db, query.since)

@router.get("/{signature_id}", response_model=SignatureInDB)
async def get_signature(
    signature_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение конкретной сигнатуры по ID.
    """
    service = SignatureService()
    signature = await service.get_signature(db, signature_id)
    if not signature:
        raise HTTPException(status_code=404, detail="Signature not found")
    return signature
