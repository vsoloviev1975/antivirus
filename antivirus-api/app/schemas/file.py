from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .base import BaseSchema

class FileBase(BaseSchema):
    """
    Базовая схема файла. Содержит только метаданные.
    """
    name: str = Field(..., max_length=255, example="test.exe")
    content_type: str = Field(..., max_length=100, example="application/octet-stream")

class FileCreate(FileBase):
    """
    Схема для загрузки файла. Добавляет содержимое файла.
    """
    content: bytes = Field(..., example=b"file_content_bytes")
    hash_sha256: str = Field(..., max_length=64, example="a94a8fe5cc...")

class FileInDB(FileBase):
    """
    Схема файла, возвращаемая из БД.
    """
    id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    size: int = Field(..., ge=0, example=1024)
    owner_id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    created_at: datetime = Field(..., example="2023-01-01T00:00:00")
    scan_result: Optional[dict] = Field(None, example={"detected": True})

    class Config:
        orm_mode = True

class FileInResponse(BaseSchema):
    """
    Схема для ответа API с файлом.
    """
    file: FileInDB
