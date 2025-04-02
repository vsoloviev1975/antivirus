"""
Конфигурация pytest и общие фикстуры для всех тестов.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.main import app
from app.models import User, Signature, File

# Тестовая БД (используем SQLite для тестов)
TEST_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def test_db_engine():
    """Фикстура для тестового движка БД (на все время выполнения тестов)."""
    engine = create_async_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    yield engine
    engine.sync_engine.dispose()

@pytest.fixture(scope="function")
async def test_db_session(test_db_engine):
    """Фикстура для тестовой сессии БД (для каждого теста)."""
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        test_db_engine, expire_on_commit=False, class_=AsyncSession
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()
    
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
def test_client():
    """Фикстура для тестового клиента FastAPI."""
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
async def test_user(test_db_session):
    """Фикстура для тестового пользователя."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword"
    )
    test_db_session.add(user)
    await test_db_session.commit()
    return user

@pytest.fixture(scope="function")
async def test_admin(test_db_session):
    """Фикстура для тестового администратора."""
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password="hashedpassword",
        is_admin=True
    )
    test_db_session.add(admin)
    await test_db_session.commit()
    return admin

@pytest.fixture(scope="function")
async def test_signature(test_db_session, test_user):
    """Фикстура для тестовой сигнатуры."""
    signature = Signature(
        threat_name="Test Threat",
        first_bytes=b"\x01\x02\x03\x04",
        remainder_hash="a94a8fe5cc...",
        remainder_length=10,
        file_type="exe",
        creator_id=test_user.id
    )
    test_db_session.add(signature)
    await test_db_session.commit()
    return signature
