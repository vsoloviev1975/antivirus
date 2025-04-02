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
    remainder_length INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    offset_start INTEGER,
    offset_end INTEGER,
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
    size INTEGER NOT NULL,
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
    remainder_length INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    offset_start INTEGER,
    offset_end INTEGER,
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