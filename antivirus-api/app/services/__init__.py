"""
Экспорт всех сервисов для удобного импорта.
Пример использования:
    from app.services import auth, user, signature
"""

from .auth import AuthService, get_current_user, get_current_admin
from .user import UserService
from .signature import SignatureService
from .scanner import FileScanner
from .digital_signature import DigitalSignatureService
from .file import FileService

__all__ = [
    'AuthService',
    'UserService',
    'SignatureService',
    'FileScanner',
    'DigitalSignatureService',
    'FileService',
    'get_current_user',
    'get_current_admin'
]
