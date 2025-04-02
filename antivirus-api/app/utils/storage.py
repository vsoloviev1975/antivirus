import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import StorageException

class StorageHelper:
    """
    Утилита для работы с файловым хранилищем.
    Поддерживает операции с временными файлами и постоянным хранилищем.
    """
    
    def __init__(self):
        self.temp_dir = Path(settings.TEMP_DIR)
        self.storage_dir = Path(settings.STORAGE_DIR)
        self._ensure_dirs_exist()
    
    def _ensure_dirs_exist(self):
        """Создает необходимые директории, если они не существуют."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(
        self,
        upload_file: UploadFile,
        permanent: bool = False
    ) -> Tuple[Path, str]:
        """
        Сохраняет загруженный файл во временное или постоянное хранилище.
        
        :param upload_file: Файл для сохранения
        :param permanent: Если True, сохраняет в постоянное хранилище
        :return: Кортеж (путь к файлу, хэш содержимого)
        """
        try:
            content = await upload_file.read()
            file_hash = self._calculate_hash(content)
            
            target_dir = self.storage_dir if permanent else self.temp_dir
            file_path = target_dir / f"{file_hash}_{upload_file.filename}"
            
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            return file_path, file_hash
        except Exception as e:
            raise StorageException(f"Failed to save file: {str(e)}")
    
    def get_file_path(self, file_hash: str) -> Optional[Path]:
        """
        Находит файл по его хэшу в хранилище.
        
        :param file_hash: Хэш содержимого файла
        :return: Путь к файлу или None если не найден
        """
        for storage_file in self.storage_dir.glob(f"{file_hash}_*"):
            if storage_file.exists():
                return storage_file
        return None
    
    def cleanup_temp_files(self, older_than_days: int = 1):
        """
        Удаляет старые временные файлы.
        
        :param older_than_days: Удалять файлы старше указанного количества дней
        """
        for temp_file in self.temp_dir.iterdir():
            if temp_file.is_file():
                file_age = (time.time() - temp_file.stat().st_mtime) / (24 * 3600)
                if file_age > older_than_days:
                    try:
                        temp_file.unlink()
                    except:
                        continue
    
    def _calculate_hash(self, content: bytes) -> str:
        """Вычисляет SHA256 хэш содержимого файла."""
        return hashlib.sha256(content).hexdigest()
    
    def move_to_permanent_storage(self, temp_path: Path) -> Path:
        """
        Перемещает файл из временного в постоянное хранилище.
        
        :param temp_path: Путь к временному файлу
        :return: Новый путь к файлу в постоянном хранилище
        """
        if not temp_path.exists():
            raise StorageException("Source file does not exist")
        
        file_hash = self._calculate_hash(temp_path.read_bytes())
        new_path = self.storage_dir / f"{file_hash}_{temp_path.name}"
        
        try:
            shutil.move(str(temp_path), str(new_path))
            return new_path
        except Exception as e:
            raise StorageException(f"Failed to move file: {str(e)}")
