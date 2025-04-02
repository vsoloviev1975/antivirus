"""
Главный конфигурационный файл Alembic.
Содержит логику выполнения миграций и подключения к БД.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.base import Base  # Импортируем все модели через базовый класс

# Конфигурация Alembic
config = context.config

# Настройка логгера
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Устанавливаем URL БД из настроек
config.set_main_option("sqlalchemy.url", settings.POSTGRES_URL)

# Указываем целевые метаданные (из Base)
target_metadata = Base.metadata

def run_migrations_offline():
    """
    Запуск миграций в offline режиме (без подключения к БД).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Включение сравнения типов колонок
        compare_server_default=True  # Сравнение значений по умолчанию
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """
    Запуск миграций в online режиме (с подключением к БД).
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True  # Учет схем БД
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
