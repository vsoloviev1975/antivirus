import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.exceptions import InvalidSignature
from app.core.config import settings
from app.core.exceptions import SignatureValidationException

class DigitalSignatureService:
    """
    Сервис для работы с электронно-цифровыми подписями (ЭЦП).
    Обеспечивает генерацию и проверку подписей для сигнатур.
    """
    
    def generate_signature(self, data: dict) -> bytes:
        """
        Генерация ЭЦП для данных сигнатуры.
        """
        private_key = load_pem_private_key(
            settings.SIGNATURE_PRIVATE_KEY.encode(),
            password=None
        )
        
        data_str = self._prepare_data_string(data)
        data_hash = hashlib.sha256(data_str.encode()).digest()
        
        signature = private_key.sign(
            data_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    def verify_signature(self, signature: bytes, data: dict) -> bool:
        """
        Проверка валидности ЭЦП для данных сигнатуры.
        """
        public_key = load_pem_public_key(settings.SIGNATURE_PUBLIC_KEY.encode())
        data_str = self._prepare_data_string(data)
        data_hash = hashlib.sha256(data_str.encode()).digest()
        
        try:
            public_key.verify(
                signature,
                data_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            raise SignatureValidationException("Неверная электронная подпись")

    def _prepare_data_string(self, data: dict) -> str:
        """
        Подготовка строки данных для подписи.
        Формат: поле1|поле2|...|полеN
        """
        fields = [
            str(data.get('threat_name', '')),
            data.get('first_bytes', b'').hex(),
            str(data.get('remainder_hash', '')),
            str(data.get('file_type', '')),
            str(data.get('offset_start', '')),
            str(data.get('offset_end', ''))
        ]
        return "|".join(fields)
