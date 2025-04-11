-- Скрипт инициализации базы данных Antivirus API
-- Создает схему, таблицы, индексы и администратора
-- Все объекты создаются только если они не существуют

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

-- 2. Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS antivirus.users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP
);

COMMENT ON TABLE antivirus.users IS 'Пользователи системы';
COMMENT ON COLUMN antivirus.users.id IS 'Уникальный идентификатор';
COMMENT ON COLUMN antivirus.users.is_admin IS 'Флаг администратора';

-- 3. Создание таблицы сигнатур
CREATE TABLE IF NOT EXISTS antivirus.signatures (
    id UUID PRIMARY KEY,
    threat_name VARCHAR(255) NOT NULL,
    first_bytes BYTEA NOT NULL,
    remainder_hash VARCHAR(64) NOT NULL,
    remainder_length INT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    offset_start INT,
    offset_end INT,
    digital_signature BYTEA NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTUAL',
    creator_id UUID NOT NULL REFERENCES antivirus.users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE antivirus.signatures IS 'Антивирусные сигнатуры';
COMMENT ON COLUMN antivirus.signatures.first_bytes IS 'Первые 8 байт сигнатуры';
COMMENT ON COLUMN antivirus.signatures.remainder_hash IS 'SHA256 хэш остатка сигнатуры';

-- 4. Создание таблицы файлов
CREATE TABLE IF NOT EXISTS antivirus.files (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    content BYTEA NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size INT NOT NULL,
    hash_sha256 VARCHAR(64) NOT NULL,
    scan_result JSONB,
    owner_id UUID NOT NULL REFERENCES antivirus.users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE antivirus.files IS 'Загруженные файлы для сканирования';

-- 5. Создание таблицы истории сигнатур
CREATE TABLE IF NOT EXISTS antivirus.signatures_history (
    history_id UUID PRIMARY KEY,
    signature_id UUID NOT NULL,
    version_created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    -- Все поля из таблицы signatures
    threat_name VARCHAR(255) NOT NULL,
    first_bytes BYTEA NOT NULL,
    remainder_hash VARCHAR(64) NOT NULL,
    remainder_length INT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    offset_start INT,
    offset_end INT,
    digital_signature BYTEA NOT NULL,
    status VARCHAR(20) NOT NULL,
    creator_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

COMMENT ON TABLE antivirus.signatures_history IS 'История изменений сигнатур';

-- 6. Создание таблицы аудита
CREATE TABLE IF NOT EXISTS antivirus.audit_log (
    audit_id UUID PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    operation_type VARCHAR(20) NOT NULL,
    operation_at TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES antivirus.users(id),
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT
);

COMMENT ON TABLE antivirus.audit_log IS 'Лог изменений в системе';

-- 7. Создание индексов
DO $$
BEGIN
    -- Индекс для поиска сигнатур по типу файла
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'antivirus'
        AND tablename = 'signatures'
        AND indexname = 'idx_signatures_file_type'
    ) THEN
        CREATE INDEX idx_signatures_file_type ON antivirus.signatures(file_type);
    END IF;

    -- Индекс для поиска в истории по ID сигнатуры
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'antivirus'
        AND tablename = 'signatures_history'
        AND indexname = 'idx_history_signature_id'
    ) THEN
        CREATE INDEX idx_history_signature_id ON antivirus.signatures_history(signature_id);
    END IF;
END
$$;

-- 8. Создание администратора (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM antivirus.users
        WHERE username = 'admin'
    ) THEN
        INSERT INTO antivirus.users (
            id,
            username,
            email,
            hashed_password,
            is_admin,
            created_at,
            updated_at
        ) VALUES (
            gen_random_uuid(),
            'admin',
            'admin@example.com',
            -- Пароль: admin123 (хеш bcrypt)
            '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
            TRUE,
            NOW(),
            NOW()
        );
        RAISE NOTICE 'Администратор создан (логин: admin, пароль: admin123)';
    ELSE
        RAISE NOTICE 'Пользователь admin уже существует';
    END IF;
END
$$;

-- 9. Создание функции для обновления updated_at
CREATE OR REPLACE FUNCTION antivirus.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 10. Создание триггеров для автообновления updated_at
DO $$
DECLARE
    tbl RECORD;
BEGIN
    FOR tbl IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'antivirus'
        AND table_name IN ('users', 'signatures', 'files')
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS trg_update_timestamp ON antivirus.%I;
            CREATE TRIGGER trg_update_timestamp
            BEFORE UPDATE ON antivirus.%I
            FOR EACH ROW EXECUTE FUNCTION antivirus.update_timestamp();
        ', tbl.table_name, tbl.table_name);
    END LOOP;
END
$$;
file_storage

# Установка зависимостей
pip install -r requirements.txt

# Применение миграций
alembic upgrade head

# Запуск сервера
uvicorn app.main:app --reload

create database file_storage;


DROP TABLE  IF EXISTS antivirus.files CASCADE;
DROP TABLE  IF EXISTS antivirus.signatures CASCADE;
DROP TABLE  IF EXISTS antivirus.history CASCADE;
DROP TABLE  IF EXISTS antivirus.audit CASCADE;


CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

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

-- 4. Создаем таблицу history
CREATE TABLE IF NOT EXISTS antivirus.history
(
	 history_id SERIAL PRIMARY KEY,
	 version_created_at TIMESTAMP NOT NULL DEFAULT Now(),
	 signature_id UUID NOT NULL REFERENCES antivirus.signatures(id) MATCH SIMPLE ON UPDATE CASCADE ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
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
drop FUNCTION antivirus.files_iud( _name TEXT, _content BYTEA, _scan_result JSON , _id UUID)

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


DROP FUNCTION IF EXISTS antivirus.scan_file_with_rabin_karp(UUID,UUID);
CREATE OR REPLACE FUNCTION antivirus.scan_file_with_rabin_karp(
    p_file_id UUID,                  -- id файла для сканирования
    p_signature_id UUID DEFAULT NULL -- id сигнатуры для сканирования, если NULL, то сканируем всеми сигнатурами
) RETURNS JSONB AS $$
DECLARE
    v_file_content BYTEA;               -- Содержимое файла в бинарном формате
    v_file_size INT;                    -- Размер файла в байтах
    v_scan_result JSONB := '[]'::JSONB; -- Результаты сканирования
    v_signature_record RECORD;          -- Данные текущей сигнатуры
    v_base BIGINT := 256;               -- Основание для полиномиального хэша
    v_mod BIGINT := 1000000007;         -- Модуль для хэш-функции
    v_power BIGINT := 1;                -- base^(window_size-1) mod mod
    v_target_hash BIGINT;               -- Хэш первых байт сигнатуры
    v_current_hash BIGINT := 0;         -- Текущий хэш скользящего окна
    v_window_size INT;                  -- Размер окна сравнения (определяется динамически)
    v_i INT;                            -- Счетчики циклов
    v_j INT;
    v_match_found BOOLEAN;              -- Флаг совпадения
    v_remainder_content BYTEA;          -- Хвост сигнатуры из файла
    v_remainder_hash TEXT;              -- MD5 хэш хвоста
    v_offset_start INT;                 -- Смещение начала сигнатуры
    v_offset_end INT;                   -- Смещение конца сигнатуры
    v_result_entry JSONB;               -- Запись результата
    v_file_info_json JSONB;             -- Возврат результата
    v_cursor CURSOR FOR                 -- Курсор для выборки сигнатур
        SELECT * FROM antivirus.signatures
        WHERE status = 'ACTUAL'
        AND (p_signature_id IS NULL OR id = p_signature_id);
BEGIN
    -- Получаем содержимое файла
    SELECT content, size INTO v_file_content, v_file_size
    FROM antivirus.files
    WHERE id = p_file_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Файл с ID % не найден', p_file_id;
    END IF;

    -- Перебираем все сигнатуры (или конкретную)
    FOR v_signature_record IN v_cursor LOOP
        -- Определяем размер окна по длине first_bytes
        v_window_size := length(v_signature_record.first_bytes);

        -- Пересчитываем power для текущего размера окна
        v_power := 1;
        FOR i IN 1..(v_window_size-1) LOOP
            v_power := (v_power * v_base) % v_mod;
        END LOOP;

        -- Вычисляем хэш первых байт сигнатуры
        v_target_hash := 0;
        FOR i IN 1..v_window_size LOOP
            IF i <= length(v_signature_record.first_bytes) THEN
                v_target_hash := (v_target_hash * v_base + ascii(substring(v_signature_record.first_bytes from i for 1))) % v_mod;
            END IF;
        END LOOP;

        -- Ищем вхождение первых байт в файле
        v_offset_start := position(v_signature_record.first_bytes::bytea in v_file_content);

        IF v_offset_start > 0 THEN
            -- Проверяем остаток сигнатуры
            v_remainder_content := substring(v_file_content
                from v_offset_start + v_window_size
                for v_signature_record.remainder_length);

            v_remainder_hash := md5(v_remainder_content);

            -- Проверяем совпадение хэша остатка
            v_match_found := (v_remainder_hash = v_signature_record.remainder_hash);

            -- Проверяем смещения
            IF v_match_found AND v_signature_record.offset_start IS NOT NULL THEN
                v_offset_start := v_offset_start - 1; -- преобразуем в 0-based индекс
                v_offset_end := v_offset_start + v_window_size + v_signature_record.remainder_length - 1;

                IF v_offset_start < v_signature_record.offset_start OR
                   (v_signature_record.offset_end IS NOT NULL AND
                    v_offset_end > v_signature_record.offset_end) THEN
                    v_match_found := FALSE;
                END IF;
            END IF;
        ELSE
            v_match_found := FALSE;
        END IF;

        -- Формируем запись результата
        v_result_entry := jsonb_build_object(
            'signatureId', v_signature_record.id,
            'threatName', v_signature_record.threat_name,
            'offsetFromStart', CASE WHEN v_match_found THEN (v_offset_start - 1) ELSE NULL END,
            'offsetFromEnd', CASE WHEN v_match_found THEN
                (v_offset_start + v_window_size + v_signature_record.remainder_length - 1)
                ELSE NULL END,
            'matched', v_match_found
        );

        -- Добавляем запись в результаты
        v_scan_result := v_scan_result || v_result_entry;
    END LOOP;

    -- Сохраняем результаты сканирования
    UPDATE antivirus.files
    SET scan_result = v_scan_result,
        updated_at = NOW()
    WHERE id = p_file_id;
	-- Получения данных таблицы для возврата результата из функции
    SELECT
		json_build_object(
			'id', id,
			'name', name,
			'size', size,
			'scan_result', scan_result,
			'created_at', created_at,
			'updated_at', updated_at
		) as file_info INTO v_file_info_json
	FROM antivirus.files
	WHERE id = p_file_id;

    RETURN v_file_info_json;
END;
$$ LANGUAGE plpgsql
COST 100;

COMMENT ON FUNCTION antivirus.scan_file_with_rabin_karp(UUID, UUID) IS 'Функция сканирования файлов с алгоритмом Рабина-Карпа';
