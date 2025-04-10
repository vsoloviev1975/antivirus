from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from uuid import UUID
from pathlib import Path
import uvicorn
from typing import List, Optional
from fastapi.responses import JSONResponse
from database import check_and_create_postgres_db, get_database_engine, create_tables
from dbengine import call_files_iud_function, get_file_info_json, get_all_files_json, delete_file_id


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
        # Если передан файл - сохраняем его временно
        file_path = None
        if file:
            temp_dir = Path("temp_files")
            temp_dir.mkdir(exist_ok=True)
            file_path = temp_dir / file.filename
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

        # Вызов функции обработки
        result_uuid = call_files_iud_function(
            name=name,
            file_path=str(file_path) if file_path else None
        )

        # Удаляем временный файл если он был
        if file_path and file_path.exists():
            file_path.unlink()

        return {"file_id": str(result_uuid)}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
"""
Получает информацию о файле по его UUID
- **file_id**: UUID файла в базе данных
"""
@app.get("/files/{file_id}")
async def get_file_info(file_id: str):
    try:
        print("RUN get_file_info")
        file_uuid = UUID(file_id)
        file_info = get_file_info_json(file_uuid)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        return file_info
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
"""
Получает список всех файлов из базы данных
Возвращает массив объектов с информацией о файлах
"""
@app.get("/allfiles", response_model=List[dict])
async def get_all_files():
    try:
        print("RUN get_all_files_json")
        files = get_all_files_json()
        if files is None:
            return JSONResponse(content=[], status_code=200)
        return files
    except Exception as e:
        print(f"API error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
"""
Удаляет файл в базе данных
- **file_id**: UUID файла для удаления
"""
@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    try:
        print("RUN delete_file")
        file_uuid = UUID(file_id)
        deleted_id = delete_file_id(file_uuid)
        print("Delete file: ", str(deleted_id))
        if deleted_id is None:
            return {"deleted_file_id": "File not found"}
            raise HTTPException(status_code=404, detail="File not found")
        return {"deleted_file_id": str(deleted_id)}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    