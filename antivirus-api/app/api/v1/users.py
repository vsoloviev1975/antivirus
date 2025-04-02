"""
Роутер для управления пользователями.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserInDB, UserUpdate
from app.api.dependencies import get_db, CurrentAdmin, CurrentUser
from app.services.user import UserService

router = APIRouter(tags=["users"])

@router.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя.
    """
    service = UserService()
    return await service.create_user(db, user_data)

@router.get("/me", response_model=UserInDB)
async def read_current_user(
    current_user: CurrentUser = Depends()
):
    """
    Получение данных текущего пользователя.
    """
    return current_user

@router.get("/", response_model=list[UserInDB])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: CurrentAdmin = Depends()
):
    """
    Получение списка всех пользователей (только для админов).
    """
    service = UserService()
    return await service.list_users(db)

@router.patch("/{user_id}", response_model=UserInDB)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: CurrentAdmin = Depends()
):
    """
    Обновление данных пользователя (только для админов).
    """
    service = UserService()
    return await service.update_user(db, user_id, user_data)
