-- Создание БД
-- CREATE DATABASE file_storage;

-- Расширение работы с UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- Расширение криптографические функции
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
CREATE TABLE antivirus.history (
    history_id BIGSERIAL PRIMARY KEY,
    version_created_at  TIMESTAMP NOT NULL
) INHERITS (antivirus.signatures);

COMMENT ON TABLE antivirus.history IS 'Изменения таблицы antivirus.signatures';
COMMENT ON COLUMN antivirus.history.history_id  IS 'Уникальный идентификатор записи в истории';
COMMENT ON COLUMN antivirus.history.version_created_at  IS 'Момент времени, когда появилась эта версия';

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
        SELECT * FROM ONLY antivirus.signatures
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
            'offsetFromStart', CASE WHEN v_match_found THEN (v_offset_start) ELSE NULL END,
            'offsetFromEnd', CASE WHEN v_match_found THEN
                (v_offset_start + v_window_size + v_signature_record.remainder_length)
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

-- DROP FUNCTION IF EXISTS antivirus.signatures_iud(JSON);
CREATE OR REPLACE FUNCTION antivirus.signatures_iud(p_data JSON)
RETURNS UUID AS $$
DECLARE
    v_id UUID;
    v_threat_name TEXT;
    v_first_bytes VARCHAR(8);
    v_remainder_hash VARCHAR(64);
    v_remainder_length INT;
    v_file_type TEXT;
    v_offset_start INT;
    v_offset_end INT;
    v_digital_signature BYTEA;
    v_status TEXT;
    v_record_exists BOOLEAN;
    v_keys TEXT[];
BEGIN
    -- Извлекаем ID из JSON (может быть NULL для новой записи)
    v_id := (p_data->>'id')::UUID;

    -- Проверяем, существует ли запись с таким ID
    IF v_id IS NOT NULL THEN
        SELECT EXISTS(SELECT 1 FROM ONLY antivirus.signatures WHERE id = v_id) INTO v_record_exists;
    ELSE
        v_record_exists := FALSE;
    END IF;

    -- Получаем ключи JSON как массив
    SELECT array_agg(key) INTO v_keys FROM jsonb_object_keys(p_data::jsonb) AS key;

    -- Если ID не указан или запись не существует - создаем новую
    IF v_id IS NULL OR NOT v_record_exists THEN
        -- Проверяем обязательные поля для создания новой записи
        IF NOT (p_data::jsonb ? 'threat_name' AND
                p_data::jsonb ? 'first_bytes' AND
                p_data::jsonb ? 'remainder_hash' AND
                p_data::jsonb ? 'remainder_length' AND
                p_data::jsonb ? 'file_type') THEN
            RAISE EXCEPTION 'Для создания новой сигнатуры необходимо указать threat_name, first_bytes, remainder_hash, remainder_length и file_type';
        END IF;

        -- Извлекаем значения из JSON
        v_threat_name := p_data->>'threat_name';
        v_first_bytes := p_data->>'first_bytes';
        v_remainder_hash := p_data->>'remainder_hash';
        v_remainder_length := (p_data->>'remainder_length')::INT;
        v_file_type := p_data->>'file_type';
        v_offset_start := (p_data->>'offset_start')::INT;
        v_offset_end := (p_data->>'offset_end')::INT;
        v_status := COALESCE(p_data->>'status', 'ACTUAL');

        -- Вставляем новую запись
        INSERT INTO antivirus.signatures (
            id,
            threat_name,
            first_bytes,
            remainder_hash,
            remainder_length,
            file_type,
            offset_start,
            offset_end,
            status,
            updated_at
        ) VALUES (
            COALESCE(v_id, gen_random_uuid()),
            v_threat_name,
            v_first_bytes,
            v_remainder_hash,
            v_remainder_length,
            v_file_type,
            v_offset_start,
            v_offset_end,
            v_status,
            NOW()
        ) RETURNING id INTO v_id;

    -- Если указан только ID - удаляем запись
    ELSEIF array_length(v_keys, 1) = 1 AND v_keys[1] = 'id' THEN
        DELETE FROM ONLY antivirus.signatures WHERE id = v_id;

    -- Если запись существует и есть поля для обновления
    ELSE
        -- Формируем динамический UPDATE с учетом только переданных полей
        EXECUTE format('
            UPDATE ONLY antivirus.signatures SET
                threat_name = COALESCE(%L, threat_name),
                first_bytes = COALESCE(%L, first_bytes),
                remainder_hash = COALESCE(%L, remainder_hash),
                remainder_length = COALESCE(%L, remainder_length),
                file_type = COALESCE(%L, file_type),
                offset_start = COALESCE(%L, offset_start),
                offset_end = COALESCE(%L, offset_end),
                status = COALESCE(%L, status),
                updated_at = NOW()
            WHERE id = %L
            RETURNING id',
            p_data->>'threat_name',
            p_data->>'first_bytes',
            p_data->>'remainder_hash',
            (p_data->>'remainder_length')::INT,
            p_data->>'file_type',
            (p_data->>'offset_start')::INT,
            (p_data->>'offset_end')::INT,
            p_data->>'status',
            v_id
        ) INTO v_id;
    END IF;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION antivirus.signatures_iud(JSON) IS 'Функция для добавления/изменения/удаления записей в таблице signatures на основе входного JSON';
--DROP FUNCTION IF EXISTS antivirus.trf_signatures_history_biud() CASCADE;
CREATE OR REPLACE FUNCTION antivirus.trf_signatures_history_biud()
  RETURNS trigger AS
$BODY$
DECLARE
BEGIN

IF TG_OP = 'DELETE' THEN
    -- при удалении не удаляем запись, а обновляем status на DELETED, пишем новое время действия
    UPDATE ONLY antivirus.signatures
        SET status = 'DELETED',
            updated_at = clock_timestamp()
    WHERE id = OLD.id;
    -- с текущей записью больше ничего не делаем
    RETURN NULL;
ELSIF TG_OP = 'UPDATE' THEN
    IF NEW.status = 'DELETED' AND OLD.status = 'DELETED' THEN
        RAISE EXCEPTION 'Невозможно обновить удалённую запись без восстановления.';
    END IF;
    -- предотвращаем срабатывание триггера на пустые обновления
    IF  NEW.id IS DISTINCT FROM OLD.id OR
        NEW.threat_name IS DISTINCT FROM OLD.threat_name OR
        NEW.first_bytes IS DISTINCT FROM OLD.first_bytes OR
        NEW.remainder_hash IS DISTINCT FROM OLD.remainder_hash OR
        NEW.remainder_length IS DISTINCT FROM OLD.remainder_length OR
        NEW.file_type IS DISTINCT FROM OLD.file_type OR
        NEW.offset_start IS DISTINCT FROM OLD.offset_start OR
        NEW.offset_end IS DISTINCT FROM OLD.offset_end OR
        NEW.digital_signature IS DISTINCT FROM OLD.digital_signature OR
        NEW.status IS DISTINCT FROM OLD.status
    THEN
        -- при обновлении пишем новое время действия
        NEW.updated_at := clock_timestamp();
        -- вставляем в history предыдущее состояние
        -- поле version_created_at - время предыдущего действия, поэтому берём его из OLD.updated_at
        INSERT INTO antivirus.history (id, threat_name, first_bytes, remainder_hash, remainder_length, file_type
                                , offset_start, offset_end, digital_signature, status, updated_at, version_created_at)
        SELECT OLD.id, OLD.threat_name, OLD.first_bytes, OLD.remainder_hash, OLD.remainder_length, OLD.file_type
             , OLD.offset_start, OLD.offset_end, OLD.digital_signature, OLD.status, OLD.updated_at, OLD.updated_at;
        -- записываем новое состояние
        RETURN NEW;
    END IF;

    RETURN NULL;
ELSIF TG_OP = 'INSERT' THEN
    -- при вставке предыдущего значения нет в history ничего не пишем
    RETURN NEW;
END IF;

END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION antivirus.trf_signatures_history_biud()
  OWNER TO postgres;
GRANT EXECUTE ON FUNCTION antivirus.trf_signatures_history_biud() TO public;
GRANT EXECUTE ON FUNCTION antivirus.trf_signatures_history_biud() TO postgres;
COMMENT ON FUNCTION antivirus.trf_signatures_history_biud() IS 'Триггерная функция версионировании записей таблицы antivirus.signatures';


DROP TRIGGER IF EXISTS tr_signatures_history_biud ON antivirus.signatures;

CREATE TRIGGER tr_signatures_history_biud
  BEFORE INSERT OR UPDATE OR DELETE
  ON antivirus.signatures
  FOR EACH ROW
  EXECUTE PROCEDURE antivirus.trf_signatures_history_biud();
COMMENT ON TRIGGER tr_signatures_history_biud ON antivirus.signatures IS 'Триггер версионировании записей таблицы antivirus.signatures';


--DROP FUNCTION IF EXISTS antivirus.trf_signatures_history_biud() CASCADE;
CREATE OR REPLACE FUNCTION antivirus.trf_audit_aiu()
  RETURNS trigger AS
$BODY$
DECLARE
    new_row jsonb := '{}';
    old_row jsonb := '{}';
BEGIN


IF TG_OP = 'UPDATE' THEN
    -- обрабатываем удаление записи
    IF NEW.status = 'DELETED' THEN
        INSERT INTO antivirus.audit (signature_id, changed_by, change_type, changed_at, fields_changed)
        VALUES (NEW.id, DEFAULT, 'DELETED', NEW.updated_at, json_build_object('NEW', null, 'OLD', row_to_json(NEW)));
    ELSE
        -- добавляем только изменённые поля
        IF NEW.id IS DISTINCT FROM OLD.id THEN
            SELECT old_row || jsonb_build_object('id', OLD.id), new_row || jsonb_build_object('id', NEW.id) INTO old_row, new_row;
        END IF;
        IF NEW.threat_name IS DISTINCT FROM OLD.threat_name THEN
            SELECT old_row || jsonb_build_object('threat_name', OLD.threat_name), new_row || jsonb_build_object('threat_name', NEW.threat_name) INTO old_row, new_row;
        END IF;
        IF NEW.first_bytes IS DISTINCT FROM OLD.first_bytes THEN
            SELECT old_row || jsonb_build_object('first_bytes', OLD.first_bytes), new_row || jsonb_build_object('first_bytes', NEW.first_bytes) INTO old_row, new_row;
        END IF;
        IF NEW.remainder_hash IS DISTINCT FROM OLD.remainder_hash THEN
            SELECT old_row || jsonb_build_object('remainder_hash', OLD.remainder_hash), new_row || jsonb_build_object('remainder_hash', NEW.remainder_hash) INTO old_row, new_row;
        END IF;
        IF NEW.remainder_length IS DISTINCT FROM OLD.remainder_length THEN
            SELECT old_row || jsonb_build_object('remainder_length', OLD.remainder_length), new_row || jsonb_build_object('remainder_length', NEW.remainder_length) INTO old_row, new_row;
        END IF;
        IF NEW.file_type IS DISTINCT FROM OLD.file_type THEN
            SELECT old_row || jsonb_build_object('file_type', OLD.file_type), new_row || jsonb_build_object('file_type', NEW.file_type) INTO old_row, new_row;
        END IF;
        IF NEW.offset_start IS DISTINCT FROM OLD.offset_start THEN
            SELECT old_row || jsonb_build_object('offset_start', OLD.offset_start), new_row || jsonb_build_object('offset_start', NEW.offset_start) INTO old_row, new_row;
        END IF;
        IF NEW.offset_end IS DISTINCT FROM OLD.offset_end THEN
            SELECT old_row || jsonb_build_object('offset_end', OLD.offset_end), new_row || jsonb_build_object('offset_end', NEW.offset_end) INTO old_row, new_row;
        END IF;
        IF NEW.digital_signature IS DISTINCT FROM OLD.digital_signature THEN
            SELECT old_row || jsonb_build_object('digital_signature', OLD.digital_signature), new_row || jsonb_build_object('digital_signature', NEW.digital_signature) INTO old_row, new_row;
        END IF;
        IF NEW.status IS DISTINCT FROM OLD.status THEN
            SELECT old_row || jsonb_build_object('status', OLD.status), new_row || jsonb_build_object('status', NEW.status) INTO old_row, new_row;
        END IF;
        IF NEW.updated_at IS DISTINCT FROM OLD.updated_at THEN
            SELECT old_row || jsonb_build_object('updated_at', OLD.updated_at), new_row || jsonb_build_object('updated_at', NEW.updated_at) INTO old_row, new_row;
        END IF;
        -- обрали изменённые данные, пишем в audit
        INSERT INTO antivirus.audit (signature_id, changed_by, change_type, changed_at, fields_changed)
        VALUES (OLD.id, DEFAULT, 'UPDATED', OLD.updated_at, json_build_object('NEW', new_row, 'OLD', old_row));
    END IF;

ELSIF TG_OP = 'INSERT' THEN
    -- пишем audit
    INSERT INTO antivirus.audit (signature_id, changed_by, change_type, changed_at, fields_changed)
    VALUES (NEW.id, DEFAULT, 'CREATED', NEW.updated_at, json_build_object('NEW', row_to_json(NEW), 'OLD', null));
    -- обрабатываем вставку удалённой записи
    IF NEW.status = 'DELETED' THEN
        INSERT INTO antivirus.audit (signature_id, changed_by, change_type, changed_at, fields_changed)
        VALUES (NEW.id, DEFAULT, 'DELETED', NEW.updated_at, json_build_object('NEW', null, 'OLD', row_to_json(NEW)));
    END IF;
END IF;


RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION antivirus.trf_audit_aiu()
  OWNER TO postgres;
GRANT EXECUTE ON FUNCTION antivirus.trf_audit_aiu() TO public;
GRANT EXECUTE ON FUNCTION antivirus.trf_audit_aiu() TO postgres;
COMMENT ON FUNCTION antivirus.trf_audit_aiu() IS 'Триггерная функция аудита записей таблицы antivirus.signatures';


DROP TRIGGER IF EXISTS tr_audit_aiu ON antivirus.signatures;
CREATE TRIGGER tr_audit_aiu
  AFTER INSERT OR UPDATE
  ON antivirus.signatures
  FOR EACH ROW
  EXECUTE PROCEDURE antivirus.trf_audit_aiu();
COMMENT ON TRIGGER tr_audit_aiu ON antivirus.signatures IS 'Триггер аудита записей таблицы antivirus.signatures';
