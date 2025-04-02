"""
Экспорт всех схем для удобного импорта в других модулях.
Пример использования:
    from app.schemas import UserCreate, UserInDB, SignatureCreate
"""

from .user import UserBase, UserCreate, UserUpdate, UserInDB, UserInResponse
from .signature import (
    SignatureBase,
    SignatureCreate,
    SignatureUpdate,
    SignatureInDB,
    SignatureInResponse,
    SignatureDiffQuery
)
from .file import FileBase, FileCreate, FileInDB, FileInResponse
from .token import Token, TokenPayload

__all__ = [
    'UserBase', 'UserCreate', 'UserUpdate', 'UserInDB', 'UserInResponse',
    'SignatureBase', 'SignatureCreate', 'SignatureUpdate', 'SignatureInDB', 
    'SignatureInResponse', 'SignatureDiffQuery',
    'FileBase', 'FileCreate', 'FileInDB', 'FileInResponse',
    'Token', 'TokenPayload'
]
