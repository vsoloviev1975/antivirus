from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from .base import BaseSchema
from app.core.config import settings

class SignatureBase(BaseSchema):
    """
    Базовая схема антивирусной сигнатуры.
    """
    threat_name: str = Field(..., max_length=255, example="EICAR-Test-File")
    first_bytes: bytes = Field(..., example=b"\x24\x45\x49\x43\x41\x52\x2D\x53")
    remainder_hash: str = Field(..., max_length=64, example="a94a8fe5cc...")
    remainder_length: int = Field(..., gt=0, example=68)
    file_type: str = Field(..., max_length=50, example="executable")
    offset_start: Optional[int] = Field(None, ge=0, example=0)
    offset_end: Optional[int] = Field(None, ge=0, example=100)

class SignatureCreate(SignatureBase):
    """
    Схема для создания новой сигнатуры.
    Наследует все обязательные поля из базовой схемы.
    """
    pass

class SignatureUpdate(BaseSchema):
    """
    Схема для обновления сигнатуры. Все поля опциональны.
    """
    threat_name: Optional[str] = Field(None, max_length=255)
    remainder_hash: Optional[str] = Field(None, max_length=64)
    remainder_length: Optional[int] = Field(None, gt=0)
    file_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, regex="^(ACTUAL|DELETED|CORRUPTED)$")

class SignatureInDB(SignatureBase):
    """
    Схема сигнатуры, возвращаемая из БД.
    """
    id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    digital_signature: bytes = Field(..., example=b"signature_bytes")
    status: str = Field(..., example="ACTUAL")
    creator_id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    created_at: datetime = Field(..., example="2023-01-01T00:00:00")
    updated_at: datetime = Field(..., example="2023-01-01T00:00:00")

    class Config:
        orm_mode = True

class SignatureInResponse(BaseSchema):
    """
    Схема для ответа API с сигнатурой.
    """
    signature: SignatureInDB

class SignatureDiffQuery(BaseSchema):
    """
    Схема для запроса изменений сигнатур.
    """
    since: datetime = Field(
        ..., 
        example="2023-01-01T00:00:00",
        description="Дата, начиная с которой нужно получить изменения"
    )
