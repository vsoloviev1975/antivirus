from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from .config import settings
from typing import AsyncGenerator

# Базовый класс для всех моделей
Base = declarative_base()

class DatabaseSessionManager:
    """
    Менеджер сессий БД для асинхронной работы с PostgreSQL.
    """
    
    def __init__(self):
        self._engine = None
        self._sessionmaker = None
    
    def init(self, url: str):
        """Инициализация подключения к БД"""
        self._engine = create_async_engine(
            url,
            pool_pre_ping=True,           # Проверка соединения перед использованием
            echo=settings.DEBUG           # Логирование SQL в debug режиме
        )
        self._sessionmaker = sessionmaker(
            self._engine, 
            expire_on_commit=False,       # Не очищать объекты после коммита
            class_=AsyncSession
        )
    
    async def close(self):
        """Закрытие соединений с БД"""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None
    
    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Генератор сессий для использования в Depends().
        Гарантирует закрытие сессии после завершения работы.
        """
        if self._sessionmaker is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")
        
        async with self._sessionmaker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

# Инициализация менеджера сессий
sessionmanager = DatabaseSessionManager()
sessionmanager.init(settings.POSTGRES_URL)

# Функция для внедрения зависимостей FastAPI
async def get_db():
    async for session in sessionmanager.get_db():
        yield session
