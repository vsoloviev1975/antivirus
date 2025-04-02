"""
Инициализация пакета приложения.
Экспортирует основные компоненты для удобного импорта.
"""

__version__ = "1.0.0"  # Версия приложения
__author__ = "Your Name <your.email@example.com>"

# Экспорт основных компонентов
from .main import app  # FastAPI приложение
from .core.config import settings  # Настройки приложения

__all__ = [
    'app',
    'settings'
]

print(f"Initializing Antivirus API v{__version__}")  # Лог инициализации
