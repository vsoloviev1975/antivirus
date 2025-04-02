import hashlib
from typing import List, Optional
from app.models.signature import Signature
from app.schemas.signature import SignatureInDB

class RabinKarp:
    """
    Реализация алгоритма Рабина-Карпа для поиска сигнатур в файлах.
    Оптимизирован для работы с бинарными данными и большими файлами.
    """
    
    def __init__(self, base: int = 256, prime: int = 101):
        """
        Инициализация алгоритма.
        
        :param base: Основание системы счисления (количество возможных символов)
        :param prime: Простое число для модульной арифметики
        """
        self.base = base
        self.prime = prime
    
    def find_signatures(
        self, 
        data: bytes, 
        signatures: List[SignatureInDB],
        chunk_size: int = 8192
    ) -> List[SignatureInDB]:
        """
        Поиск сигнатур в данных с использованием алгоритма Рабина-Карпа.
        
        :param data: Бинарные данные для сканирования
        :param signatures: Список сигнатур для поиска
        :param chunk_size: Размер блока обработки (для больших файлов)
        :return: Список найденных сигнатур
        """
        found_signatures = []
        
        # Предварительно вычисляем хэши первых байт всех сигнатур
        sig_hashes = {
            self._hash_bytes(sig.first_bytes[:8]): sig
            for sig in signatures
        }
        
        # Вычисляем BASE^(m-1) % prime для эффективного обновления хэша
        h = pow(self.base, 8 - 1, self.prime)
        
        current_hash = 0
        window = bytearray(8)
        
        for i, byte in enumerate(data):
            # Обновляем скользящее окно
            window_pos = i % 8
            if i >= 8:
                # Удаляем влияние самого старого байта
                current_hash = (current_hash - window[window_pos] * h) % self.prime
            
            # Добавляем новый байт
            window[window_pos] = byte
            current_hash = (current_hash * self.base + byte) % self.prime
            
            # Проверяем совпадение хэша
            if i >= 7 and current_hash in sig_hashes:
                sig = sig_hashes[current_hash]
                if self._verify_full_match(data, i-7, sig):
                    found_signatures.append(sig)
        
        return found_signatures
    
    def _hash_bytes(self, data: bytes) -> int:
        """Вычисление хэша для блока байт."""
        h = 0
        for byte in data:
            h = (h * self.base + byte) % self.prime
        return h
    
    def _verify_full_match(
        self,
        data: bytes,
        start_pos: int,
        signature: SignatureInDB
    ) -> bool:
        """
        Проверка полного совпадения сигнатуры с данными.
        
        :param data: Исходные данные
        :param start_pos: Позиция начала предполагаемого совпадения
        :param signature: Проверяемая сигнатура
        :return: True если полное совпадение найдено
        """
        # Проверка первых 8 байт
        first_bytes = data[start_pos:start_pos+8]
        if first_bytes != signature.first_bytes[:8]:
            return False
        
        # Проверка "хвоста" сигнатуры
        remainder_start = start_pos + 8
        remainder_end = remainder_start + signature.remainder_length
        
        if remainder_end > len(data):
            return False
        
        remainder = data[remainder_start:remainder_end]
        remainder_hash = hashlib.sha256(remainder).hexdigest()
        
        return remainder_hash == signature.remainder_hash
