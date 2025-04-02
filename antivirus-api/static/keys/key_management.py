"""
Утилиты для управления ключами ЭЦП.
Проверяет наличие и валидность ключей при старте приложения.
"""

import os
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from app.core.exceptions import SecurityException

class KeyManager:
    def __init__(self, keys_dir: str = "static/keys"):
        self.keys_dir = Path(keys_dir)
        self.private_key_path = self.keys_dir / "private_key.pem"
        self.public_key_path = self.keys_dir / "public_key.pem"
        
        # Проверяем существование директории
        if not self.keys_dir.exists():
            self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        self._validate_keys()

    def _validate_keys(self):
        """Проверка наличия и валидности ключей."""
        if not self.private_key_path.exists():
            raise SecurityException("Private key not found")
        
        if not self.public_key_path.exists():
            raise SecurityException("Public key not found")
        
        try:
            # Проверка чтения ключей
            self.load_private_key()
            self.load_public_key()
        except Exception as e:
            raise SecurityException(f"Invalid key format: {str(e)}")

    def load_private_key(self):
        """Загрузка приватного ключа."""
        with open(self.private_key_path, "rb") as key_file:
            return serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )

    def load_public_key(self):
        """Загрузка публичного ключа."""
        with open(self.public_key_path, "rb") as key_file:
            return serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )

    @staticmethod
    def generate_key_pair(key_dir: str = "static/keys"):
        """
        Генерация новой пары ключей (для админских задач).
        Использовать только при инициализации системы!
        """
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        key_dir = Path(key_dir)
        key_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерация приватного ключа
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Сохранение приватного ключа
        with open(key_dir / "private_key.pem", "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Генерация и сохранение публичного ключа
        public_key = private_key.public_key()
        with open(key_dir / "public_key.pem", "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        # Установка правильных прав доступа
        os.chmod(key_dir / "private_key.pem", 0o600)
        os.chmod(key_dir / "public_key.pem", 0o644)
