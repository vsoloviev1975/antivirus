"""
Инициализация модуля статических файлов.
Регистрирует утилиты для работы с ключами и временными файлами.
"""

from pathlib import Path
from .keys.key_management import KeyManager
from .temp.temp_file_manager import TempFileManager

# Инициализация менеджеров при импорте модуля
key_manager = KeyManager()
temp_file_manager = TempFileManager()

__all__ = [
    'key_manager',
    'temp_file_manager'
]