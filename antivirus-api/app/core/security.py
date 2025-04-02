import os
from pathlib import Path
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from typing import Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from .config import settings
from .exceptions import (
    InvalidCredentialsException,
    InsufficientPermissionsException
)

# Контекст для хеширования паролей
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12  # Количество раундов хеширования
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка соответствия пароля и его хеша.
    Возвращает True если пароль верный.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Генерация хеша пароля"""
    return pwd_context.hash(password)

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Создание JWT токена.
    
    Args:
        data: Данные для включения в токен (обычно user_id и роли)
        expires_delta: Время жизни токена (по умолчанию из настроек)
    
    Returns:
        Подписанный JWT токен
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    ))
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )

def decode_token(token: str) -> dict:
    """
    Декодирование JWT токена с проверкой подписи.
    Вызывает InvalidCredentialsException при ошибке.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise InvalidCredentialsException(detail=str(e))

# Функции для работы с ключами ЭЦП
def load_key_file(key_path: str) -> bytes:
    """Загрузка ключа из файла с проверкой существования"""
    path = Path(key_path)
    if not path.exists():
        raise FileNotFoundError(f"Key file not found: {key_path}")
    return path.read_bytes()

def get_private_key() -> bytes:
    """Получение приватного ключа для ЭЦП"""
    return load_key_file(settings.SIGNATURE_PRIVATE_KEY_PATH)

def get_public_key() -> bytes:
    """Получение публичного ключа для верификации ЭЦП"""
    return load_key_file(settings.SIGNATURE_PUBLIC_KEY_PATH)
