"""
Тесты для сервиса аутентификации.
"""

import pytest
from app.services.auth import AuthService
from app.services.user import UserService
from app.core.security import get_password_hash
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_authenticate_user_success(test_db_session, test_user):
    """Тест успешной аутентификации пользователя."""
    auth_service = AuthService(UserService())
    
    # Обновляем пароль пользователя на известный хэш
    test_user.hashed_password = get_password_hash("password")
    test_db_session.add(test_user)
    await test_db_session.commit()
    
    authenticated_user = await auth_service.authenticate_user(
        test_db_session, "testuser", "password"
    )
    assert authenticated_user is not None
    assert authenticated_user.username == "testuser"

@pytest.mark.asyncio
async def test_authenticate_user_failure(test_db_session):
    """Тест неудачной аутентификации."""
    auth_service = AuthService(UserService())
    
    user = await auth_service.authenticate_user(
        test_db_session, "nonexistent", "wrongpassword"
    )
    assert user is None

@pytest.mark.asyncio
async def test_create_access_token(test_user):
    """Тест создания JWT токена."""
    auth_service = AuthService(UserService())
    token = await auth_service.create_access_token(test_user)
    
    assert token is not None
    assert isinstance(token, str)
