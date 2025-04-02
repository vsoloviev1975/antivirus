from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from .base import BaseSchema

class UserBase(BaseSchema):
    """
    Базовая схема пользователя. Содержит только публичные данные.
    """
    username: str = Field(..., min_length=3, max_length=50, example="johndoe")
    email: EmailStr = Field(..., example="user@example.com")

class UserCreate(UserBase):
    """
    Схема для создания пользователя. Добавляет пароль.
    """
    password: str = Field(..., min_length=8, max_length=50, example="strongpassword")

class UserUpdate(BaseSchema):
    """
    Схема для обновления пользователя. Все поля опциональны.
    """
    email: Optional[EmailStr] = Field(None, example="newemail@example.com")
    password: Optional[str] = Field(None, min_length=8, max_length=50)
    is_active: Optional[bool] = Field(None, example=True)

class UserInDB(UserBase):
    """
    Схема пользователя, возвращаемая из БД. 
    Содержит все поля, включая служебные.
    """
    id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    is_admin: bool = Field(False, example=False)
    created_at: datetime = Field(..., example="2023-01-01T00:00:00")
    is_active: bool = Field(True, example=True)

    class Config:
        orm_mode = True

class UserInResponse(BaseSchema):
    """
    Схема для ответа API с пользователем.
    Включает базовые данные и может быть расширена.
    """
    user: UserInDB
