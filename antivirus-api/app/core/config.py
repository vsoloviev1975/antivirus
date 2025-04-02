from pydantic import BaseSettings, PostgresDsn, AnyUrl
from typing import Optional

class Settings(BaseSettings):
    """
    Конфигурация приложения. Параметры могут быть переопределены через .env файл.
    Использует pydantic для валидации типов.
    """
    
    # Настройки PostgreSQL (обязательные)
    POSTGRES_URL: PostgresDsn = "postgresql+asyncpg://user:password@localhost:5432/antivirus_db"
    
    # Настройки аутентификации
    SECRET_KEY: str = "your-secret-key-here"  # Для JWT токенов
    ALGORITHM: str = "HS256"                 # Алгоритм подписи JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30     # Время жизни токена
    
    # Настройки ЭЦП
    SIGNATURE_PRIVATE_KEY_PATH: str = "keys/private_key.pem"
    SIGNATURE_PUBLIC_KEY_PATH: str = "keys/public_key.pem"
    
    # Дополнительные настройки
    DEBUG: bool = False
    CORS_ORIGINS: list[AnyUrl] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"         # Файл с переменными окружения
        env_file_encoding = "utf-8"
        case_sensitive = True      # Чувствительность к регистру

# Экземпляр конфигурации для импорта в других модулях
settings = Settings()
