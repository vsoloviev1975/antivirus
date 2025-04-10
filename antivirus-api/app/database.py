"""
Модуль для работы с базой данных PostgreSQL
Содержит настройку подключения и базовые модели SQLAlchemy
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Создаем базовый класс для моделей
Base = declarative_base()

# Настройка подключения к PostgreSQL
def get_db_tmp_url():
    return (
        f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME_TMP}"
    )

def get_db_url():
    return (
        f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
    
# Проверяет существование базы данных PostgreSQL и создает ее при отсутствии    
def check_and_create_postgres_db() -> bool:
    try:
        # Подключаемся к серверу PostgreSQL (к системной базе 'postgres')
        temp_engine = create_engine(get_db_tmp_url())
        
        # Проверяем существование базы данных
        with temp_engine.connect() as conn:
            # Запрос для проверки существования базы
            query = text("SELECT 1 FROM pg_database WHERE datname = :dbname")
            result = conn.execute(query, {'dbname': settings.DB_NAME}).scalar()
            
            if not result:
                # Создаем базу данных, если ее нет
                conn.execution_options(isolation_level="AUTOCOMMIT")
                conn.execute(text(f"CREATE DATABASE {settings.DB_NAME}"))
                return True
            else:
                return True
                
    except ProgrammingError as e:
        print(f"Ошибка доступа: {e}")
        return False
    except OperationalError as e:
        print(f"Ошибка подключения к серверу PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return False
    finally:
        if 'temp_engine' in locals():
            temp_engine.dispose()

# Возвращает engine для работы с указанной базой данных
def get_database_engine():
    try:
        engine = create_engine(get_db_url())
        # Проверяем подключение
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None            

# Создаем движок SQLAlchemy
engine = get_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создает объекты в базе данных через raw SQL
def create_tables():
    
    tables_sql = [
        """
        -- Добавляем расширение работы с UUID
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp"
        SCHEMA public
        VERSION "1.1";
        """,
        """
        -- 1. Создание схемы (если не существует)
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.schemata
                WHERE schema_name = 'antivirus'
            ) THEN
                CREATE SCHEMA antivirus;
                COMMENT ON SCHEMA antivirus IS 'Схема для антивирусного API';
                RAISE NOTICE 'Схема antivirus создана';
            ELSE
                RAISE NOTICE 'Схема antivirus уже существует';
            END IF;
        END
        $$;
        """,
        """
        -- 2. Создание таблицы файлов
        CREATE TABLE IF NOT EXISTS antivirus.files (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name TEXT NOT NULL,
            content BYTEA NOT NULL,
            size INT NOT NULL,
            scan_result JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        COMMENT ON TABLE antivirus.files IS 'Загруженные файлы';
        COMMENT ON COLUMN antivirus.files.id IS 'Id файла в формате UUID';
        COMMENT ON COLUMN antivirus.files.name IS 'Имя файла';
        COMMENT ON COLUMN antivirus.files.content IS 'Содержание файла';
        COMMENT ON COLUMN antivirus.files.size IS 'Размер файла';
        COMMENT ON COLUMN antivirus.files.scan_result IS 'Результат сканирования с разными сигнатурами';
        COMMENT ON COLUMN antivirus.files.created_at IS 'Дата и время добавления файла';
        COMMENT ON COLUMN antivirus.files.updated_at IS 'Дата и время изменения файла';
        """,
        """
        -- 3. Создание таблицы сигнатур
        CREATE TABLE IF NOT EXISTS antivirus.signatures (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            threat_name TEXT NOT NULL,
            first_bytes VARCHAR(8) NOT NULL,
            remainder_hash VARCHAR(64) NOT NULL,
            remainder_length INT NOT NULL,
            file_type TEXT NOT NULL,
            offset_start INT,
            offset_end INT,
            digital_signature BYTEA DEFAULT NULL,
            status TEXT NOT NULL DEFAULT 'ACTUAL',
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        COMMENT ON TABLE antivirus.signatures IS 'Антивирусные сигнатуры';
        COMMENT ON COLUMN antivirus.signatures.id IS 'id сигнатуры в формате UUID';
        COMMENT ON COLUMN antivirus.signatures.threat_name IS 'Название угрозы';
        COMMENT ON COLUMN antivirus.signatures.first_bytes IS 'Первые 8 байт';
        COMMENT ON COLUMN antivirus.signatures.remainder_hash IS 'Хэш хвоста';
        COMMENT ON COLUMN antivirus.signatures.remainder_length IS 'Длина хвоста';
        COMMENT ON COLUMN antivirus.signatures.file_type IS 'Тип файла';
        COMMENT ON COLUMN antivirus.signatures.offset_start IS 'Смещение начала сигнатуры';
        COMMENT ON COLUMN antivirus.signatures.offset_end IS 'Смещение конца сигнатуры';
        COMMENT ON COLUMN antivirus.signatures.digital_signature IS 'ЭЦП';
        COMMENT ON COLUMN antivirus.signatures.status IS 'Статус записи';
        COMMENT ON COLUMN antivirus.signatures.updated_at IS 'Время изменения записи';
        """,
        """
        -- 4. Создаем таблицу history
        CREATE TABLE IF NOT EXISTS antivirus.history
        (
             history_id SERIAL PRIMARY KEY,
             signature_id UUID NOT NULL REFERENCES antivirus.signatures(id) MATCH SIMPLE ON UPDATE CASCADE ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
             version_created_at TIMESTAMP NOT NULL DEFAULT Now(),
             threat_name TEXT NOT NULL,
             first_bytes VARCHAR(8) NOT NULL,
             remainder_hash VARCHAR(64) NOT NULL,
             remainder_length INT NOT NULL,
             file_type TEXT NOT NULL,
             offset_start INT NOT NULL,
             offset_end INT NOT NULL,
             digital_signature TEXT,
             status TEXT NOT NULL,
             updated_at TIMESTAMP
        );
        COMMENT ON TABLE antivirus.history IS 'История изменения сигнатур';
        COMMENT ON COLUMN antivirus.history.history_id IS 'Уникальный идентификатор записи в истории';
        COMMENT ON COLUMN antivirus.history.signature_id IS 'Ссылка на запись в таблице сигнатур (тот же id, что и в основной таблице)';
        COMMENT ON COLUMN antivirus.history.version_created_at IS 'Момент времени, когда появилась эта версия';
        COMMENT ON COLUMN antivirus.history.threat_name IS 'Название угрозы (копия поля на момент сохранения в истории)';
        COMMENT ON COLUMN antivirus.history.first_bytes IS 'Первые 8 байт (копия поля)';
        COMMENT ON COLUMN antivirus.history.remainder_hash IS 'Хэш хвоста (копия поля)';
        COMMENT ON COLUMN antivirus.history.remainder_length IS 'Длина хвоста (копия поля)';
        COMMENT ON COLUMN antivirus.history.file_type IS 'Тип файла (копия поля)';
        COMMENT ON COLUMN antivirus.history.offset_start IS 'Смещение начала сигнатуры (копия поля)';
        COMMENT ON COLUMN antivirus.history.offset_end IS 'Смещение конца сигнатуры (копия поля)';
        COMMENT ON COLUMN antivirus.history.digital_signature IS 'Копия ЭЦП';
        COMMENT ON COLUMN antivirus.history.status IS 'Копия статуса записи на момент сохранения версии';
        COMMENT ON COLUMN antivirus.history.updated_at IS 'Копия значения updated_at из таблицы сигнатур';
        """,
        """
        -- 5. Создаем таблицу audit
        CREATE TABLE IF NOT EXISTS antivirus.audit
        (
            audit_id SERIAL PRIMARY KEY,
            signature_id UUID NOT NULL REFERENCES antivirus.signatures(id) MATCH SIMPLE ON UPDATE CASCADE ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
            changed_by	TEXT NOT NULL DEFAULT SESSION_USER,
            change_type	TEXT,
            changed_at TIMESTAMP NOT NULL DEFAULT Now(),
            fields_changed JSONB
        );
        COMMENT ON TABLE antivirus.audit IS 'Таблица аудита';
        COMMENT ON COLUMN antivirus.audit.audit_id IS 'Уникальный идентификатор записи в аудите';
        COMMENT ON COLUMN antivirus.audit.signature_id IS 'Ссылка на запись в таблице сигнатур';
        COMMENT ON COLUMN antivirus.audit.changed_by IS 'Указатель на пользователя, совершившего изменение';
        COMMENT ON COLUMN antivirus.audit.change_type IS 'Тип изменения (CREATED, UPDATED, DELETED, CORRUPTED и т.д.)';
        COMMENT ON COLUMN antivirus.audit.changed_at IS 'Время, когда произошло изменение';
        COMMENT ON COLUMN antivirus.audit.fields_changed IS 'Список изменённых полей, можно хранить в виде JSON';
        """,
        """
        CREATE OR REPLACE FUNCTION antivirus.files_iud( _name TEXT DEFAULT NULL, _content BYTEA DEFAULT NULL, _scan_result JSON DEFAULT NULL, _id UUID DEFAULT NULL)
          RETURNS uuid AS
        $BODY$
            DECLARE
            uid UUID;
        BEGIN
                if _id isnull then
                    if _name isnull and _content isnull then
                        raise exception 'Не указано имя файла или его содержимое';
                    end if;
                    insert into antivirus.files(name, content, size)
                        values(_name, _content, octet_length(_content))
                    returning id into uid;
                    return uid;
                end if;

                if _name notnull then
                    update antivirus.files set
                        name = CASE
                                WHEN _name isnull or _name = name THEN name
                                ELSE _name END
                    where id = _id;
                end if;

                if _content notnull then
                    update antivirus.files set
                        content = CASE
                                WHEN _content isnull or _content = content THEN content
                                ELSE _content END,
                        size = CASE
                                WHEN _content isnull THEN size
                                ELSE octet_length(_content) END
                    where id = _id;
                end if;

                if _scan_result notnull then
                    update antivirus.files set
                        scan_result = CASE
                                      WHEN _scan_result isnull or _scan_result = scan_result THEN scan_result
                                      ELSE _scan_result END
                    where id = _id;
                end if;

                if _name isnull and _content isnull and _scan_result isnull then
                    delete from antivirus.files where id = _id;
                end if;

                return _id;
        END
        $BODY$
        LANGUAGE plpgsql VOLATILE
        COST 100;

        COMMENT ON FUNCTION antivirus.files_iud(TEXT, BYTEA, JSON, UUID) IS 'Функция записи/обновления/удаления файла';
        """
    ]

    with engine.connect() as conn:
        for sql in tables_sql:
            conn.execute(text(sql))
        conn.commit()
# Генератор сессий для Dependency Injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Экспортируем Base для использования в моделях
__all__ = ['Base', 'engine', 'get_db', 'create_tables']
