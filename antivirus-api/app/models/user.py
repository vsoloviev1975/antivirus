from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    """
    Модель пользователя системы.
    Содержит информацию для аутентификации и авторизации.
    """
    __tablename__ = 'users'
    __table_args__ = {'comment': 'Пользователи системы'}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment='Уникальный идентификатор'
    )
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        comment='Логин пользователя'
    )
    email = Column(
        String(100),
        unique=True,
        nullable=False,
        comment='Email пользователя'
    )
    hashed_password = Column(
        String(255),
        nullable=False,
        comment='Хэшированный пароль'
    )
    is_admin = Column(
        Boolean,
        default=False,
        nullable=False,
        comment='Флаг администратора'
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment='Активен ли пользователь'
    )
    last_login = Column(
        DateTime,
        nullable=True,
        comment='Последний вход в систему'
    )

    def __repr__(self):
        return f'<User {self.username}>'
