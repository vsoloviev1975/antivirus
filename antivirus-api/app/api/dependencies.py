"""
Зависимости API и инициализация роутеров.
Содержит общие зависимости для всех эндпоинтов.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password
from app.models.user import User
from app.schemas.token import TokenPayload
from app.services import (
    AuthService,
    UserService,
    FileService,
    SignatureService
)
from app.services.auth import get_current_user, get_current_admin

# Базовые роутеры для разных разделов API
auth_router = APIRouter()
users_router = APIRouter()
files_router = APIRouter()
signatures_router = APIRouter()

# OAuth2 схема для аутентификации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def common_parameters(
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Общие зависимости для всех эндпоинтов.
    Возвращает словарь с общими параметрами.
    """
    return {
        "db": db,
        "user_service": UserService(),
        "auth_service": AuthService(UserService()),
        "file_service": FileService(),
        "signature_service": SignatureService()
    }

CommonDep = Annotated[dict, Depends(common_parameters)]

async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    commons: CommonDep = Depends()
) -> User:
    """
    Зависимость для получения текущего активного пользователя.
    Проверяет валидность токена и активность пользователя.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await commons["user_service"].get_by_id(
        commons["db"], 
        token_data.sub
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return user

async def get_current_active_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Зависимость для проверки прав администратора.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

# Типы для аннотаций зависимостей
CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentAdmin = Annotated[User, Depends(get_current_active_admin)]
