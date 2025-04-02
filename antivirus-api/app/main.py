"""
Главный файл приложения - точка входа FastAPI.
Интегрирует все компоненты системы: API, БД, сервисы, утилиты.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Импорт всех необходимых компонентов
from app.core.config import settings
from app.core.database import engine, Base, sessionmanager
from app.core.security import validate_ecp_keys
from app.utils.rabin_karp import RabinKarp
from app.utils.storage import TempFileManager
from app.services import (
    AuthService,
    UserService,
    SignatureService,
    FileService,
    ScannerService
)
from app.api import api_router
from app.models import User, Signature, File, AuditLog, SignatureHistory

# Настройка логгера
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    Обрабатывает startup и shutdown события.
    """
    # Startup логика
    logger.info("Starting Antivirus API...")
    
    try:
        # Инициализация подключения к БД
        async with engine.begin() as conn:
            if settings.DEBUG:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables verified/created")
        
        # Проверка ключей ЭЦП
        validate_ecp_keys()
        logger.info("Digital signature keys validated")
        
        # Инициализация сервисов
        init_services()
        logger.info("All services initialized")
        
        yield  # Здесь приложение работает
        
    finally:
        # Shutdown логика
        logger.info("Shutting down Antivirus API...")
        await sessionmanager.close()
        logger.info("Database connections closed")

def init_services():
    """Инициализация всех сервисов приложения."""
    # Инициализация утилит
    RabinKarp.init_base_params()
    TempFileManager.init_temp_dirs()
    
    # Инициализация сервисов с зависимостями
    user_service = UserService()
    auth_service = AuthService(user_service)
    signature_service = SignatureService()
    file_service = FileService()
    scanner_service = ScannerService()
    
    # Можно добавить в контейнер зависимостей
    services = {
        "user_service": user_service,
        "auth_service": auth_service,
        "signature_service": signature_service,
        "file_service": file_service,
        "scanner_service": scanner_service,
    }
    
    return services

def create_app() -> FastAPI:
    """
    Фабрика для создания экземпляра FastAPI приложения.
    
    Returns:
        FastAPI: Сконфигурированное приложение со всеми зависимостями
    """
    app = FastAPI(
        title="Antivirus API",
        description="Сервис для антивирусного сканирования файлов с использованием сигнатурного анализа",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
    )
    
    # Настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Подключение главного роутера API
    app.include_router(
        api_router,
        prefix=settings.API_V1_STR,
    )
    
    # Health check endpoint
    @app.get("/health", include_in_schema=False)
    async def health_check():
        return {"status": "OK", "version": "1.0.0"}
    
    return app

# Создание экземпляра приложения
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
