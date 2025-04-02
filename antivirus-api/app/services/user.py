from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from app.core.exceptions import NotFoundException

class UserService:
    """
    Сервис для работы с пользователями.
    Обрабатывает CRUD операции и бизнес-логику, связанную с пользователями.
    """
    
    async def get_by_id(
        self,
        db: AsyncSession,
        user_id: str
    ) -> Optional[User]:
        """
        Получение пользователя по ID.
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_username(
        self,
        db: AsyncSession,
        username: str
    ) -> Optional[User]:
        """
        Получение пользователя по имени пользователя.
        """
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def create_user(
        self,
        db: AsyncSession,
        user_data: UserCreate
    ) -> User:
        """
        Создание нового пользователя.
        """
        hashed_password = get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_user(
        self,
        db: AsyncSession,
        user_id: str,
        user_data: UserUpdate
    ) -> User:
        """
        Обновление данных пользователя.
        """
        values = user_data.dict(exclude_unset=True)
        if "password" in values:
            values["hashed_password"] = get_password_hash(values.pop("password"))
        
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**values)
        )
        await db.commit()
        
        user = await self.get_by_id(db, user_id)
        if not user:
            raise NotFoundException("Пользователь не найден")
        return user
