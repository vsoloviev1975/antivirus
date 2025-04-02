"""
Тесты для API работы с файлами.
"""

import pytest
from fastapi import status
from io import BytesIO

@pytest.mark.asyncio
async def test_upload_file(test_client, test_user, auth_headers):
    """Тест загрузки файла."""
    # Создаем тестовый файл в памяти
    test_file = BytesIO(b"test file content")
    test_file.name = "test.txt"
    
    response = test_client.post(
        "/api/v1/files/upload",
        files={"file": test_file},
        headers=auth_headers(test_user.id)
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.json()
    assert response.json()["name"] == "test.txt"

@pytest.mark.asyncio
async def test_get_file_list(test_client, test_user, auth_headers):
    """Тест получения списка файлов пользователя."""
    response = test_client.get(
        "/api/v1/files/",
        headers=auth_headers(test_user.id)
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_file_unauthorized(test_client, test_user, test_admin, auth_headers):
    """Тест попытки доступа к чужому файлу."""
    # Админ загружает файл
    admin_file = BytesIO(b"admin file content")
    admin_file.name = "admin.txt"
    
    upload_response = test_client.post(
        "/api/v1/files/upload",
        files={"file": admin_file},
        headers=auth_headers(test_admin.id)
    )
    file_id = upload_response.json()["id"]
    
    # Обычный пользователь пытается получить файл
    response = test_client.get(
        f"/api/v1/files/{file_id}",
        headers=auth_headers(test_user.id)
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
