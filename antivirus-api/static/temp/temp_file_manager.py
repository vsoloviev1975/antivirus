"""
Менеджер временных файлов.
Обеспечивает безопасное создание и автоматическую очистку временных файлов.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.exceptions import StorageException

class TempFileManager:
    def __init__(self, temp_root: str = "static/temp"):
        self.temp_root = Path(temp_root)
        self.uploads_dir = self.temp_root / "uploads"
        self.scans_dir = self.temp_root / "scans"
        
        self._init_directories()
    
    def _init_directories(self):
        """Инициализация директорий с проверкой прав доступа."""
        try:
            self.temp_root.mkdir(parents=True, exist_ok=True)
            self.uploads_dir.mkdir(exist_ok=True)
            self.scans_dir.mkdir(exist_ok=True)
            
            # Установка безопасных прав доступа
            self.temp_root.chmod(0o700)
            self.uploads_dir.chmod(0o700)
            self.scans_dir.chmod(0o700)
        except Exception as e:
            raise StorageException(f"Failed to init temp directories: {str(e)}")
    
    def create_temp_file(self, prefix: str, suffix: str = "", directory: str = "uploads") -> Path:
        """
        Создает временный файл с уникальным именем.
        
        :param prefix: Префикс имени файла
        :param suffix: Суффикс (расширение) файла
        :param directory: Поддиректория (uploads/scans)
        :return: Path к созданному файлу
        """
        try:
            dir_path = self.temp_root / directory
            dir_path.mkdir(exist_ok=True)
            
            timestamp = int(time.time())
            temp_file = dir_path / f"{prefix}_{timestamp}{suffix}"
            temp_file.touch()
            temp_file.chmod(0o600)
            
            return temp_file
        except Exception as e:
            raise StorageException(f"Failed to create temp file: {str(e)}")
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Очистка старых временных файлов.
        
        :param max_age_hours: Максимальный возраст файлов в часах
        """
        cutoff_time = time.time() - max_age_hours * 3600
        
        for temp_dir in [self.uploads_dir, self.scans_dir]:
            for item in temp_dir.iterdir():
                try:
                    if item.is_file() and item.stat().st_mtime < cutoff_time:
                        item.unlink()
                except Exception:
                    continue
    
    def get_file_path(self, filename: str, directory: str) -> Optional[Path]:
        """
        Безопасное получение пути к временному файлу.
        
        :param filename: Имя файла
        :param directory: Поддиректория (uploads/scans)
        :return: Path или None если файл не существует или путь небезопасен
        """
        try:
            dir_path = self.temp_root / directory
            file_path = dir_path / filename
            
            # Проверка, что файл действительно находится внутри целевой директории
            if not file_path.resolve().parent.samefile(dir_path.resolve()):
                return None
                
            return file_path if file_path.exists() else None
        except:
            return None
