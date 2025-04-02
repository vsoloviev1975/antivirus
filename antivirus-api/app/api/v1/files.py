"""
Роутер для работы с файлами.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.file import FileInDB
from app.api.dependencies import get_db, CurrentUser
from app.services.file import FileService

router = APIRouter(tags=["files"])

@router.post("/upload", response_model=FileInDB, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends()
):
    """
    Загрузка файла на сервер.
    """
    service = FileService()
    try:
        content = await file.read()
        return await service.create_file(db, {
            "name": file.filename,
            "content": content,
            "content_type": file.content_type
        }, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await file.close()

@router.get("/", response_model=list[FileInDB])
async def list_user_files(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends()
):
    """
    Получение списка файлов текущего пользователя.
    """
    service = FileService()
    return await service.get_user_files(db, current_user.id)

@router.get("/{file_id}", response_model=FileInDB)
async def get_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends()
):
    """
    Получение информации о конкретном файле.
    """
    service = FileService()
    file = await service.get_file(db, file_id)
    if not file or file.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="File not found")
    return file
