from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User
from app.schemas.token import TokenPayload
from app.db.dependencies import get_db
from app.services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class AuthService:
    """
    Сервис для аутентификации и авторизации пользователей.
    Обрабатывает логин, создание токенов и проверку прав доступа.
    """
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def authenticate_user(
        self,
        username: str,
        password: str,
        db: AsyncSession
    ) -> User:
        """
        Аутентификация пользователя по логину и паролю.
        Возвращает пользователя или None если аутентификация не удалась.
        """
        user = await self.user_service.get_by_username(db, username)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверное имя пользователя или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    async def create_access_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Создание JWT токена для пользователя.
        """
        payload = {
            "sub": str(user.id),
            "is_admin": user.is_admin,
            "exp": datetime.utcnow() + (expires_delta or timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ))
        }
        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Зависимость для получения текущего пользователя из JWT токена.
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
            detail="Не удалось проверить учетные данные",
        )
    
    user = await UserService().get_by_id(db, token_data.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return user

async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Зависимость для проверки прав администратора.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав",
        )
    return current_user
