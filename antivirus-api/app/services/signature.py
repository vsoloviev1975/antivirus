from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.signature import Signature, SignatureHistory
from app.models.user import User
from app.schemas.signature import SignatureCreate, SignatureUpdate
from app.core.exceptions import NotFoundException, DatabaseException
from app.services.digital_signature import DigitalSignatureService

class SignatureService:
    """
    Сервис для работы с антивирусными сигнатурами.
    Обрабатывает создание, обновление, поиск и проверку сигнатур.
    """
    
    def __init__(self):
        self.digital_signature_service = DigitalSignatureService()

    async def create_signature(
        self,
        db: AsyncSession,
        signature_data: SignatureCreate,
        creator: User
    ) -> Signature:
        """
        Создание новой антивирусной сигнатуры.
        """
        signature_dict = signature_data.dict()
        signature_dict["creator_id"] = creator.id
        
        # Генерация электронной подписи
        signature_dict["digital_signature"] = (
            self.digital_signature_service.generate_signature(signature_dict)
        )
        
        signature = Signature(**signature_dict)
        db.add(signature)
        await db.commit()
        await db.refresh(signature)
        return signature

    async def get_signature(
        self,
        db: AsyncSession,
        signature_id: str
    ) -> Optional[Signature]:
        """
        Получение сигнатуры по ID.
        """
        result = await db.execute(
            select(Signature)
            .where(Signature.id == signature_id)
        )
        return result.scalars().first()

    async def get_signatures_diff(
        self,
        db: AsyncSession,
        since: datetime
    ) -> List[Signature]:
        """
        Получение измененных сигнатур с указанной даты.
        """
        result = await db.execute(
            select(Signature)
            .where(Signature.updated_at >= since)
        )
        return result.scalars().all()

    async def verify_signature(
        self,
        db: AsyncSession,
        signature_id: str
    ) -> bool:
        """
        Проверка целостности сигнатуры с помощью ЭЦП.
        """
        signature = await self.get_signature(db, signature_id)
        if not signature:
            raise NotFoundException("Сигнатура не найдена")
        
        return self.digital_signature_service.verify_signature(
            signature.digital_signature,
            signature.dict()
        )
