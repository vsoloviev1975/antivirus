"""
Пакет для работы с базой данных антивирусного сервиса

Содержит:
- database.py - настройки подключения и модели
- dbengine.py - основные функции работы с файлами
- main.py - FastAPI приложение
"""

from database import Base, engine, get_db, create_tables
from dbengine import call_files_iud_function, get_file_info_json, get_all_files_json, delete_file_id

__all__ = [
    'Base',
    'engine',
    'get_db',
    'create_tables',
    'call_files_iud_function',
    'get_file_info_json',
    'get_all_files_json',
    'delete_file_id'
]
