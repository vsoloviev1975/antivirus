from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body
from uuid import UUID
from pathlib import Path
import uvicorn
from typing import List, Optional
from fastapi.responses import JSONResponse
from database import check_and_create_postgres_db, get_database_engine, create_tables, init_db
from dbengine import call_files_iud_function, get_file_info_json, get_all_files_json, delete_file_id, call_signatures_iud_function, get_actual_signatures_json
from dbengine import get_signatures_by_guids, get_signatures_by_status, scan_file_with_rabin_karp
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime


# Настройка основного логгера приложения
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создать папку для логов
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Добавить обработчики
file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=1024*1024,  # 1 MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logger.addHandler(file_handler)
logger.addHandler(logging.StreamHandler())

app = FastAPI(title="Antivirus File Storage API")

# Инициализация базы данных при старте приложения
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Проверка и создание базы данных...")
        
        # 1. Проверяем и создаём БД (если её нет)
        if not check_and_create_postgres_db():
            logger.error("Ошибка при создании базы данных")
            raise RuntimeError("Не удалось создать базу данных")
        
        # 2. Инициализируем движок SQLAlchemy
        logger.info("Инициализация подключения к базе...")
        engine = init_db()  # Теперь движок создаётся после проверки БД
        
        # 3. Создаём таблицы
        logger.info("Создание таблиц...")
        create_tables()
        logger.info("База данных готова!")
        
    except Exception as e:
        logger.critical(f"Ошибка инициализации базы: {str(e)}", exc_info=True)
        raise RuntimeError("Не удалось запустить базу данных")
"""
Создает или обновляет файл в базе данных
- **file**: Файл для загрузки (обязательно)
"""
@app.post("/files/upload")
async def create_file_db(
    file: UploadFile = File(...)
):
    try:
        logger.info(f"Starting file upload. Filename: {file.filename}")
        
        # Создаем временную директорию, если ее нет
        temp_dir = Path("temp_files")
        temp_dir.mkdir(exist_ok=True)
        file_path = temp_dir / file.filename
        
        # Сохраняем временный файл
        logger.debug(f"Saving temporary file to: {file_path}")
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        logger.info(f"Temporary file saved. Size: {file_path.stat().st_size} bytes")

        # Вызов функции обработки с именем файла из file.filename
        logger.debug("Calling files_iud_function")
        result_uuid = call_files_iud_function(
            name=file.filename,  # Используем имя файла из объекта UploadFile
            file_path=str(file_path))
        logger.info(f"File successfully processed. UUID: {result_uuid}")

        # Удаляем временный файл
        if file_path.exists():
            logger.debug(f"Removing temporary file: {file_path}")
            file_path.unlink()
            logger.debug("Temporary file removed")

        return {"file_id": str(result_uuid)}
    
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
        
"""
Получает информацию о файле по его UUID
- **file_id**: UUID файла в базе данных
"""
@app.get("/files/{file_id}")
async def get_file_info(file_id: str):
    try:
        logger.info(f"Request received for file info. File ID: {file_id}")
        
        # Валидация UUID
        logger.debug(f"Validating UUID format: {file_id}")
        file_uuid = UUID(file_id)
        logger.debug("UUID format is valid")
        
        # Получение информации о файле
        logger.debug("Fetching file info from database")
        file_info = get_file_info_json(file_uuid)
        
        if not file_info:
            logger.warning(f"File not found in database. File ID: {file_id}")
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.info(f"Successfully retrieved file info. File: {file_info.get('name')}, Size: {file_info.get('size')} bytes")
        return file_info
        
    except ValueError as e:
        logger.error(f"Invalid UUID format: {file_id}. Error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching file {file_id}. Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.critical(f"Unexpected error fetching file {file_id}. Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
        
"""
Получает список всех файлов из базы данных
Возвращает массив объектов с информацией о файлах
"""
@app.get("/allfiles", response_model=List[dict])
async def get_all_files():
    try:
        logger.info("Starting to fetch all files from database")
        
        # Получение списка файлов
        logger.debug("Executing get_all_files_json()")
        files = get_all_files_json()
        
        if files is None:
            logger.warning("No files found in database")
            return JSONResponse(content=[], status_code=200)
        
        logger.info(f"Successfully retrieved {len(files)} files from database")
        logger.debug(f"First file in list: {files[0]['name'] if files else 'N/A'}")
        return files
        
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.critical(f"Unexpected error while fetching files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
        
"""
Удаляет файл в базе данных
- **file_id**: UUID файла для удаления
"""
@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    try:
        logger.info(f"Starting file deletion process. File ID: {file_id}")
        
        logger.debug(f"Validating UUID format: {file_id}")
        file_uuid = UUID(file_id)
        logger.debug("UUID format is valid")
        
        logger.debug("Executing delete_file_id()")
        deleted_id = delete_file_id(file_uuid)
        print("Delete file: ", str(deleted_id))
        if deleted_id is None:
            logger.warning(f"File not found for deletion. File ID: {file_id}")
            return {"deleted_file_id": "File not found for deletion."}
        logger.info(f"Successfully deleted file. Deleted File ID: {deleted_id}")
        return {"deleted_file_id": str(deleted_id)}
    except ValueError as e:
        logger.error(f"Invalid UUID format: {file_id}. Error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    except SQLAlchemyError as e:
        logger.error(f"Database error during deletion of file {file_id}. Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.critical(f"Unexpected error during file deletion {file_id}. Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
        
"""
Обрабатывает операции с антивирусными сигнатурами
- **signature_data**: JSON с данными сигнатуры
  (должен содержать либо полные данные для создания, 
   либо id и поля для обновления,
   либо только id для удаления)
"""
@app.post("/signatures/manage")
async def manage_signature(signature_data: dict):
    try:
        logger.info(f"Processing signature operation. Data: {signature_data}")
        
        # Валидация входных данных
        if not signature_data:
            logger.error("Empty signature data received")
            raise HTTPException(status_code=400, detail="Signature data cannot be empty")
        
        # Проверка наличия id для операции удаления
        if len(signature_data) == 1 and "id" in signature_data:
            logger.info(f"Signature deletion requested for ID: {signature_data['id']}")
        
        # Вызов функции обработки
        signature_id = call_signatures_iud_function(signature_data)
        
        if not signature_id:
            logger.error("Signature operation failed - no ID returned")
            raise HTTPException(status_code=500, detail="Signature operation failed")
        
        logger.info(f"Successfully processed signature. ID: {signature_id}")
        return {"signature_id": str(signature_id)}
        
    except ValueError as e:
        logger.error(f"Invalid UUID format: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
        
"""
Получает список актуальных сигнатур с возможностью фильтрации по дате обновления
- **since**: Необязательный параметр в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS) - 
             возвращаются только сигнатуры, обновленные после указанной даты
"""
@app.get("/signatures", response_model=List[dict])
async def get_actual_signatures(since: Optional[str] = None):
    try:
        logger.info(f"Request received for actual signatures. Since filter: {since}")
        
        # Парсим параметр since если он передан
        since_dt = None
        if since is not None:
            try:
                since_dt = datetime.fromisoformat(since)
                logger.debug(f"Parsed since parameter: {since_dt}")
            except ValueError as e:
                logger.error(f"Invalid since parameter format: {since}. Error: {str(e)}")
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid since parameter format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        # Получаем сигнатуры из БД
        signatures = get_actual_signatures_json(since_dt)
        
        if signatures is None:
            logger.info("No actual signatures found in database")
            return JSONResponse(content=[], status_code=200)
        
        logger.info(f"Successfully retrieved {len(signatures)} actual signatures")
        return signatures
        
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching signatures: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")
    except HTTPException:
        raise  # Пробрасываем уже обработанные HTTPException
    except Exception as e:
        logger.critical(f"Unexpected error while fetching signatures: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")        
        
"""
Получает сигнатуры по списку GUID
- **guids**: Список GUID сигнатур в теле запроса
Возвращает список объектов с информацией о сигнатурах
"""
@app.post("/signatures/guid", response_model=List[dict])
async def get_guid_signatures(guids: List[str] = Body(...)):
    try:
        logger.info(f"Request received for signatures by GUIDs. GUIDs count: {len(guids)}")
        
        # Валидация GUID
        valid_guids = []
        for guid in guids:
            try:
                valid_guids.append(UUID(guid))
            except ValueError:
                logger.warning(f"Invalid GUID format: {guid}")
                continue
                
        if not valid_guids:
            logger.error("No valid GUIDs provided")
            raise HTTPException(
                status_code=400,
                detail="No valid GUIDs provided in request"
            )
        
        # Получаем сигнатуры из БД
        signatures = get_signatures_by_guids(valid_guids)
        
        logger.info(f"Successfully retrieved {len(signatures)} signatures by GUIDs")
        return signatures
        
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching signatures by GUIDs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Unexpected error while fetching signatures by GUIDs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
        
"""
Получает сигнатуры по статусу (ACTUAL или DELETED)
- **status**: Статус сигнатур для фильтрации (обязательный параметр)
Возвращает список объектов с информацией о сигнатурах
"""
@app.get("/signatures/status", response_model=List[dict])
async def get_status_signatures(status: str):
    try:
        logger.info(f"Request received for signatures with status: {status}")
        
        # Валидация параметра status
        if status not in ('ACTUAL', 'DELETED'):
            logger.error(f"Invalid status parameter: {status}")
            raise HTTPException(
                status_code=400,
                detail="Status must be either 'ACTUAL' or 'DELETED'"
            )
        
        # Получаем сигнатуры из БД
        signatures = get_signatures_by_status(status)
        
        logger.info(f"Successfully retrieved {len(signatures)} signatures with status {status}")
        return signatures
        
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching signatures by status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Unexpected error while fetching signatures by status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")        
        
"""
Сканирует файл с использованием алгоритма Рабина-Карпа
- **file_id**: UUID файла для сканирования (обязательный)
- **signature_id**: UUID сигнатуры для сканирования (опциональный)
Возвращает результат сканирования
"""
@app.post("/files/scan", response_model=dict)
async def scan_file(
    file_id: str,
    signature_id: Optional[str] = None
):
    try:
        logger.info(f"Starting file scan. File ID: {file_id}, Signature ID: {signature_id}")
        
        # Валидация UUID файла
        try:
            file_uuid = UUID(file_id)
        except ValueError:
            logger.error(f"Invalid file UUID format: {file_id}")
            raise HTTPException(
                status_code=400,
                detail="Invalid file ID format"
            )
        
        # Валидация UUID сигнатуры (если указан)
        signature_uuid = None
        if signature_id:
            try:
                signature_uuid = UUID(signature_id)
            except ValueError:
                logger.error(f"Invalid signature UUID format: {signature_id}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid signature ID format"
                )
        
        # Вызов функции сканирования
        scan_result = scan_file_with_rabin_karp(file_uuid, signature_uuid)
        
        if not scan_result:
            logger.error(f"Scan failed for file {file_id}")
            raise HTTPException(
                status_code=404,
                detail="File not found or scan failed"
            )
        
        logger.info(f"Scan completed successfully for file {file_id}")
        return scan_result
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")        

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    