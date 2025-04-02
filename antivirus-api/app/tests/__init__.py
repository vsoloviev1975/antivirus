﻿"""
Инициализация тестового модуля.
Позволяет импортировать фикстуры и вспомогательные функции из других модулей.
"""

# Маркер для pytest, чтобы находил тесты в поддиректориях
pytest_plugins = [
    "tests.conftest",
    "tests.test_services",
    "tests.test_api"
]

__all__ = []
