from fastapi import HTTPException, status
from typing import Any, Optional

class BaseAPIException(HTTPException):
    """
    Базовый класс для кастомных исключений API.
    Все исключения должны наследоваться от него.
    """
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[dict] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class InvalidCredentialsException(BaseAPIException):
    """Ошибка аутентификации (неверные учетные данные)"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class InsufficientPermissionsException(BaseAPIException):
    """Ошибка авторизации (недостаточно прав)"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )

class NotFoundException(BaseAPIException):
    """Ресурс не найден"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

class SignatureValidationException(BaseAPIException):
    """Ошибка проверки электронной подписи"""
    def __init__(self, detail: str = "Signature validation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )

class DatabaseException(BaseAPIException):
    """Ошибка работы с базой данных"""
    def __init__(self, detail: str = "Database error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
