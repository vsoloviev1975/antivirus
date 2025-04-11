# dbengine.py
# Модуль для работы с функциями в базе данных 

from pathlib import Path
from typing import Optional, Union
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError, OperationalError
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import compiler
from psycopg2.extensions import adapt, quote_ident
from psycopg2.sql import SQL, Identifier, Literal, Composed, Composable
from sqlalchemy.sql import compiler
import logging
import json
from typing import List
from datetime import datetime


"""
Тестовая функция, показывает подготовленный SQL запрос к БД
"""
def log_final_query(query, params):
    try:
        def format_sql_value(value):
            if value is None:
                return "NULL"  # Важно: просто NULL без кавычек и типа
            elif isinstance(value, bytes):
                hex_data = value.hex()
                return f"E'\\\\x{hex_data}'::bytea"
            elif isinstance(value, (dict, list)):
                return f"'{json.dumps(value)}'::json"
            elif isinstance(value, str):
                return "'" + value.replace("'", "''") + "'"
                #return f"'{value.replace("'", "''")}'"
            else:
                return str(value)

        # Формируем полный набор параметров
        all_params = {k: params.get(k, None) for k in query._bindparams.keys()}
        # Подставляем параметры в запрос
        final_sql = query.text
        for param, value in all_params.items():
            final_sql = final_sql.replace(
                f":{param}", 
                format_sql_value(value)
            )
        print("PROPER SQL QUERY:")
        print(final_sql)

    except Exception as e:
        print(f"SQL formatting error: {str(e)}")
"""
Вызывает функцию antivirus.files_iud в PostgreSQL с автоматическим чтением файла если задан
:param name: Имя файла
:param file_path: Путь к файлу на диске (будет прочитан как bytes)
:param scan_result: Результат сканирования в виде словаря
:param file_id: UUID файла для обновления (None для создания нового)
:return: UUID созданного или обновленного файла
"""
def call_files_iud_function(
    name: str = None,
    file_path: str = None,
    scan_result: dict = None,
    file_id: UUID = None
) -> UUID:
    db = next(get_db())
    try:
        # Читаем файл если передан путь
        content = None
        if file_path is not None:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            if not file_path.is_file():
                raise ValueError(f"Указанный путь не является файлом: {file_path}")
                
            with open(file_path, 'rb') as f:
                content = f.read()

        # Подготавливаем параметры (None значения передаются как есть)
        params = {
            "_name": name,
            "_content": content,
            "_scan_result": json.dumps(scan_result) if scan_result is not None else None,
            "_id": file_id
        }

        # Формируем SQL запрос
        query = text("""
            SELECT antivirus.files_iud(
                :_name, 
                :_content, 
                :_scan_result, 
                :_id
            ) AS file_id
        """)

        # Выполняем запрос
        result = db.execute(query, params)
        file_uuid = result.scalar()
        db.commit()
        print("File post DB: "+str(file_path)+" UUID Row: ", str(file_uuid))
        return file_uuid
        
    except SQLAlchemyError as e:
        db.rollback()
        raise SQLAlchemyError(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
"""
Получает информацию о файле (без содержимого) в виде JSON
Args: file_id: UUID файла
Returns: Словарь с информацией о файле или None если файл не найден
"""
def get_file_info_json(file_id: UUID) -> Optional[dict]:
    db = next(get_db())
    print("Input get_file_info_json")
    try:
        result = db.execute(
            text("""
                SELECT 
                    json_build_object(
                        'id', id,
                        'name', name,
                        'size', size,
                        'scan_result', scan_result,
                        'created_at', created_at,
                        'updated_at', updated_at
                    ) as file_info
                FROM antivirus.files 
                WHERE id = :id
            """),
            {"id": file_id}
        )
        row = result.fetchone()
        print("Get file: ", file_id)
        return row[0] if row else None
    except SQLAlchemyError as e:
        db.rollback()
        raise
    finally:
        db.close()
"""
Получает информацию о всех файлах (без содержимого) в виде JSON
"""        
def get_all_files_json() -> Optional[List[dict]]:
    db = next(get_db())
    print("Input get_all_files_json")
    try:
        result = db.execute(
            text("""
                SELECT 
                    json_build_object(
                        'id', id::text,
                        'name', name,
                        'size', size,
                        'scan_result', scan_result,
                        'created_at', created_at,
                        'updated_at', updated_at
                    ) as file_info
                FROM antivirus.files
                ORDER BY created_at DESC
            """)
        )
        rows = result.fetchall()
        return [row[0] for row in rows] if rows else None
    except Exception as e:
        db.rollback()
        print(f"Database error: {str(e)}")
        raise
    finally:
        db.close()
"""
Удаляет файл
Args: file_id: UUID файла
Returns: :return: UUID удаленного файла
"""
def delete_file_id(file_id: UUID) -> Optional[UUID]:
    db = next(get_db())
    try:
        result = db.execute(
            text("""
                DELETE FROM antivirus.files 
                WHERE id = :id
                RETURNING id
            """),
            {"id": file_id}
        )
        deleted_id = result.scalar()
        db.commit()
        print("File Delete from DB: ", str(deleted_id))
        return deleted_id  # Вернёт None если файл не найден
    except SQLAlchemyError as e:
        db.rollback()
        raise SQLAlchemyError(f"Database error: {e}")
    finally:
        db.close()
        
"""
Вызывает функцию antivirus.signatures_iud в PostgreSQL для добавления/изменения/удаления сигнатур
:param signature_data: JSON-данные сигнатуры (dict)
:return: UUID обработанной сигнатуры
"""
def call_signatures_iud_function(signature_data: dict) -> UUID:
    db = next(get_db())
    try:
        # Преобразуем данные в JSON строку
        json_data = json.dumps(signature_data)
        
        # Формируем SQL запрос
        query = text("""
            SELECT antivirus.signatures_iud(:json_data) AS signature_id
        """)
        
        # Выполняем запрос
        result = db.execute(query, {"json_data": json_data})
        signature_uuid = result.scalar()
        db.commit()
        
        # logger.debug(f"Processed signature with ID: {signature_uuid}")
        return signature_uuid
        
    except SQLAlchemyError as e:
        db.rollback()
        # logger.error(f"Database error in signatures_iud: {str(e)}", exc_info=True)
        raise SQLAlchemyError(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        # logger.critical(f"Unexpected error in signatures_iud: {str(e)}", exc_info=True)
        raise e
    finally:
        db.close()
        
"""
Получает список актуальных сигнатур с возможностью фильтрации по дате обновления
:param since: Необязательная дата для фильтрации (только записи, обновленные после этой даты)
:return: Список словарей с информацией о сигнатурах или None если сигнатур не найдено
"""
def get_actual_signatures_json(since: Optional[datetime] = None) -> Optional[List[dict]]:
    db = next(get_db())
    try:
        # Базовый запрос
        query = """
            SELECT 
                json_build_object(
                    'id', id::text,
                    'threat_name', threat_name,
                    'first_bytes', first_bytes,
                    'remainder_hash', remainder_hash,
                    'remainder_length', remainder_length,
                    'file_type', file_type,
                    'offset_start', offset_start,
                    'offset_end', offset_end,
                    'status', status,
                    'updated_at', updated_at
                ) as signature_info
            FROM ONLY antivirus.signatures
            WHERE status = 'ACTUAL'
        """
        
        # Добавляем фильтр по дате если нужно
        params = {}
        if since is not None:
            query += " AND updated_at >= :since"
            params["since"] = since
        
        query += " ORDER BY updated_at DESC"
        
        result = db.execute(text(query), params)
        rows = result.fetchall()
        
        return [row[0] for row in rows] if rows else None
        
    except SQLAlchemyError as e:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
        
"""
Получает сигнатуры по списку GUID
:param guid_list: Список UUID сигнатур
:return: Список словарей с информацией о сигнатурах или None если сигнатуры не найдены
"""
def get_signatures_by_guids(guid_list: List[UUID]) -> Optional[List[dict]]:
    db = next(get_db())
    try:
        # Проверяем, что список не пустой
        if not guid_list:
            return []
            
        query = text("""
            SELECT 
                json_build_object(
                    'id', id::text,
                    'threat_name', threat_name,
                    'first_bytes', first_bytes,
                    'remainder_hash', remainder_hash,
                    'remainder_length', remainder_length,
                    'file_type', file_type,
                    'offset_start', offset_start,
                    'offset_end', offset_end,
                    'status', status,
                    'updated_at', updated_at
                ) as signature_info
            FROM ONLY antivirus.signatures
            WHERE id = ANY(:guid_list)
            ORDER BY updated_at DESC
        """)
        
        result = db.execute(query, {"guid_list": guid_list})
        rows = result.fetchall()
        
        return [row[0] for row in rows] if rows else []
        
    except SQLAlchemyError as e:
        db.rollback()
        raise SQLAlchemyError(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
        
"""
Получает сигнатуры по статусу (ACTUAL или DELETED)
:param status: Статус сигнатур для фильтрации
:return: Список словарей с информацией о сигнатурах или пустой список если не найдено
"""
def get_signatures_by_status(status: str) -> List[dict]:
    db = next(get_db())
    try:
        # Проверяем допустимые значения статуса
        if status not in ('ACTUAL', 'DELETED'):
            return []
            
        query = text("""
            SELECT 
                json_build_object(
                    'id', id::text,
                    'threat_name', threat_name,
                    'first_bytes', first_bytes,
                    'remainder_hash', remainder_hash,
                    'remainder_length', remainder_length,
                    'file_type', file_type,
                    'offset_start', offset_start,
                    'offset_end', offset_end,
                    'status', status,
                    'updated_at', updated_at
                ) as signature_info
            FROM ONLY antivirus.signatures
            WHERE status = :status
            ORDER BY updated_at DESC
        """)
        
        result = db.execute(query, {"status": status})
        rows = result.fetchall()
        return [row[0] for row in rows]
        
    except SQLAlchemyError:
        db.rollback()
        return []
    finally:
        db.close()
        
"""
Вызывает функцию antivirus.scan_file_with_rabin_karp для сканирования файла
:param file_id: UUID файла для сканирования (обязательный)
:param signature_id: UUID сигнатуры для сканирования (опциональный)
:return: Результат сканирования в виде словаря
"""
def scan_file_with_rabin_karp(file_id: UUID, signature_id: Optional[UUID] = None) -> dict:
    db = next(get_db())
    try:
        query = text("""
            SELECT antivirus.scan_file_with_rabin_karp(:file_id, :signature_id) as scan_result
        """)
        
        params = {
            "file_id": file_id,
            "signature_id": signature_id
        }
        
        result = db.execute(query, params)
        scan_result = result.scalar()
        db.commit()
        
        return scan_result if scan_result else {}
        
    except SQLAlchemyError:
        db.rollback()
        return {}
    finally:
        db.close()

# Экспортируем для использования в моделях
__all__ = ['call_files_iud_function', 'get_file_info_json', 'get_all_files_json', 
           'delete_file_id', 'call_signatures_iud_function', 'get_actual_signatures_json',
           'get_signatures_by_guids', 'get_signatures_by_status', 'scan_file_with_rabin_karp']        
