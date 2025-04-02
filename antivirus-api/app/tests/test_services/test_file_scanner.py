"""
Тесты для сервиса сканирования файлов.
"""

import pytest
from app.utils.rabin_karp import RabinKarp
from app.schemas.signature import SignatureInDB

@pytest.mark.asyncio
async def test_file_scanner_find_signature():
    """Тест обнаружения сигнатуры в файле."""
    scanner = RabinKarp()
    
    test_signatures = [
        SignatureInDB(
            id="1",
            threat_name="Test Signature",
            first_bytes=b"TEST1234",
            remainder_hash="hash",
            remainder_length=0,
            file_type="exe"
        )
    ]
    
    test_data = b"SOME DATA BEFORE TEST1234 SOME DATA AFTER"
    
    found = scanner.find_signatures(test_data, test_signatures)
    assert len(found) == 1
    assert found[0].threat_name == "Test Signature"

@pytest.mark.asyncio
async def test_file_scanner_no_match():
    """Тест случая, когда сигнатуры не найдены."""
    scanner = RabinKarp()
    
    test_signatures = [
        SignatureInDB(
            id="1",
            threat_name="Test Signature",
            first_bytes=b"TEST1234",
            remainder_hash="hash",
            remainder_length=0,
            file_type="exe"
        )
    ]
    
    test_data = b"NO MATCHING DATA HERE"
    
    found = scanner.find_signatures(test_data, test_signatures)
    assert len(found) == 0
