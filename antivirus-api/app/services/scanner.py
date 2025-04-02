import hashlib
from typing import List, Optional
from app.models.signature import Signature
from app.schemas.signature import SignatureInDB
from app.core.exceptions import SignatureValidationException

class FileScanner:
    """
    Сервис для сканирования файлов на наличие вредоносных сигнатур.
    Реализует алгоритм Рабина-Карпа для эффективного поиска.
    """
    
    def __init__(self, base: int = 256, prime: int = 10**9 + 7):
        self.base = base
        self.prime = prime

    async def scan_file(
        self,
        file_content: bytes,
        signatures: List[SignatureInDB]
    ) -> List[SignatureInDB]:
        """
        Сканирование файла на наличие сигнатур.
        Возвращает список обнаруженных сигнатур.
        """
        window_size = 8
        detected = []
        
        # Предварительное вычисление хэшей сигнатур
        signature_hashes = {
            self._calculate_hash(sig.first_bytes[:window_size]): sig
            for sig in signatures
        }
        
        # Инициализация переменных для алгоритма Рабина-Карпа
        current_hash = 0
        highest_power = pow(self.base, window_size - 1, self.prime)
        
        # Скользящее окно по файлу
        for i in range(len(file_content)):
            if i >= window_size:
                # Удаляем самый старый байт из хэша
                current_hash = (
                    current_hash - file_content[i - window_size] * highest_power
                ) % self.prime
            
            # Добавляем новый байт в хэш
            current_hash = (current_hash * self.base + file_content[i]) % self.prime
            
            # Проверяем совпадение хэша
            if i >= window_size - 1 and current_hash in signature_hashes:
                sig = signature_hashes[current_hash]
                if self._check_full_match(file_content, i - window_size + 1, sig):
                    detected.append(sig)
        
        return detected

    def _calculate_hash(self, data: bytes) -> int:
        """Вычисление полиномиального хэша для данных."""
        h = 0
        for byte in data:
            h = (h * self.base + byte) % self.prime
        return h

    def _check_full_match(
        self,
        file_content: bytes,
        start_pos: int,
        signature: SignatureInDB
    ) -> bool:
        """Проверка полного совпадения сигнатуры."""
        # Проверка первых байт
        if file_content[start_pos:start_pos+8] != signature.first_bytes[:8]:
            return False
        
        # Проверка хвоста сигнатуры
        remainder_start = start_pos + 8
        remainder_end = remainder_start + signature.remainder_length
        
        if remainder_end > len(file_content):
            return False
        
        remainder = file_content[remainder_start:remainder_end]
        remainder_hash = hashlib.sha256(remainder).hexdigest()
        
        return remainder_hash == signature.remainder_hash
