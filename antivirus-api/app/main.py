from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from uuid import UUID
from pathlib import Path
import uvicorn
from typing import List, Optional
from fastapi.responses import JSONResponse
from database import check_and_create_postgres_db, get_database_engine, create_tables
from dbengine import call_files_iud_function, get_file_info_json, get_all_files_json, delete_file_id
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy.exc import SQLAlchemyError


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
    if not check_and_create_postgres_db():
        raise RuntimeError("Failed to initialize database")
    engine = get_database_engine()
    if engine is None:
        raise RuntimeError("Failed to connect to database")
    create_tables()
"""
Создает или обновляет файл в базе данных
- **name**: Имя файла (обязательно)
- **file**: Файл для загрузки (опционально для обновления)
- **scan_result**: Результат сканирования в JSON (опционально)
- **file_id**: UUID файла для обновления (опционально, если не указан - создается новый)
"""
@app.post("/files/upload")
async def create_file_db(
    name: str = Form(...),
    file: UploadFile = File(None)
):
    try:
        logger.info(f"Starting file upload. Name: {name}, Filename: {file.filename if file else 'No file'}")
        
        # Если передан файл - сохраняем его временно
        file_path = None
        if file:
            temp_dir = Path("temp_files")
            temp_dir.mkdir(exist_ok=True)
            file_path = temp_dir / file.filename
            
            logger.debug(f"Saving temporary file to: {file_path}")
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            logger.info(f"Temporary file saved. Size: {file_path.stat().st_size} bytes")

        # Вызов функции обработки
        logger.debug("Calling files_iud_function")
        result_uuid = call_files_iud_function(
            name=name,
            file_path=str(file_path) if file_path else None
        )
        logger.info(f"File successfully processed. UUID: {result_uuid}")

        # Удаляем временный файл если он был
        if file_path and file_path.exists():
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    