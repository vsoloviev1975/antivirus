import hashlib
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.file import File
from app.models.user import User
from app.schemas.file import FileCreate
from app.core.exceptions import NotFoundException
from app.services.scanner import FileScanner

class FileService:
    """
    Сервис для работы с загруженными файлами.
    Обрабатывает хранение, сканирование и управление файлами.
    """
    
    def __init__(self):
        self.scanner = FileScanner()

    async def create_file(
        self,
        db: AsyncSession,
        file_data: FileCreate,
        owner: User
    ) -> File:
        """
        Сохранение файла в базе данных.
        """
        file = File(
            name=file_data.name,
            content=file_data.content,
            content_type=file_data.content_type,
            size=len(file_data.content),
            hash_sha256=hashlib.sha256(file_data.content).hexdigest(),
            owner_id=owner.id
        )
        db.add(file)
        await db.commit()
        await db.refresh(file)
        return file

    async def scan_file(
        self,
        db: AsyncSession,
        file_id: str,
        signatures: List[SignatureInDB]
    ) -> List[SignatureInDB]:
        """
        Сканирование файла на наличие вредоносных сигнатур.
        """
        file = await self.get_file(db, file_id)
        if not file:
            raise NotFoundException("Файл не найден")
        
        return await self.scanner.scan_file(file.content, signatures)

    async def get_file(
        self,
        db: AsyncSession,
        file_id: str
    ) -> Optional[File]:
        """
        Получение файла по ID.
        """
        result = await db.execute(select(File).where(File.id == file_id))
        return result.scalars().first()

    async def get_user_files(
        self,
        db: AsyncSession,
        user_id: str
    ) -> List[File]:
        """
        Получение списка файлов пользователя.
        """
        result = await db.execute(
            select(File)
            .where(File.owner_id == user_id)
            .order_by(File.created_at.desc())
        )
        return result.scalars().all()
