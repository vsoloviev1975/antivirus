"""
Модуль для работы с настройками приложения
Читает конфигурацию из переменных окружения
"""

from pydantic import BaseSettings

class Settings(BaseSettings):
    # Настройки базы данных
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_NAME_TMP: str
    
    class Config:
        env_file = "../.env"

# Создаем экземпляр настроек
settings = Settings()
