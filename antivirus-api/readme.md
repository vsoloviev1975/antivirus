# Antivirus API Service

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95.2-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)

Сервис для антивирусного сканирования файлов с использованием сигнатурного анализа и алгоритма Рабина-Карпа.

## 📌 Основные возможности

- 🔒 JWT аутентификация (Access + Refresh токены)
- 📊 Управление антивирусными сигнатурами (CRUD)
- 🔍 Сканирование файлов на наличие угроз
- 📝 Электронная подпись сигнатур (RSA)
- 🕵️‍♂️ Аудит всех изменений в системе
- 📈 Версионирование сигнатур

## 🚀 Быстрый старт

### Предварительные требования
- Python 3.10+
- PostgreSQL 14+
- Redis (опционально для кэширования)

### Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/yourrepo/antivirus-api.git
cd antivirus-api

# 2. Создать и активировать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# 3. Установить зависимости
pip install -r requirements.txt

Настройка окружения

    Скопировать .env.example в .env

    Настроить параметры подключения к БД

    Сгенерировать ключи ЭЦП:

# Создать директорию для ключей
mkdir -p static/keys

# Генерация ключей
openssl genpkey -algorithm RSA -out static/keys/private_key.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -pubout -in static/keys/private_key.pem -out static/keys/public_key.pem

# Установка прав доступа
chmod 600 static/keys/private_key.pem
chmod 644 static/keys/public_key.pem


Запуск в development режиме
uvicorn app.main:app --reload

Запуск в production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

 Документация API

После запуска сервиса доступны:

    Swagger UI: http://localhost:8000/api/docs

    ReDoc: http://localhost:8000/api/redoc

🛠 Технологический стек

    Backend: Python + FastAPI

    База данных: PostgreSQL

    Аутентификация: JWT

    Алгоритм поиска: Рабина-Карпа

    ЭЦП: RSA 2048

    Логирование: Loguru

    Тестирование: Pytest

Структура проекта

antivirus-api/
├── app/                      # Основной код приложения
│   ├── core/                 # Ядро системы
│   ├── models/               # Модели БД
│   ├── schemas/              # Pydantic схемы
│   ├── services/             # Бизнес-логика
│   ├── api/                  # API эндпоинты
│   ├── utils/                # Вспомогательные утилиты
│   └── main.py               # Точка входа
├── migrations/               # Миграции базы данных
├── static/                   # Статические файлы
│   ├── keys/                 # Ключи ЭЦП
│   └── temp/                 # Временные файлы
├── tests/                    # Тесты
├── .env                      # Переменные окружения
├── .gitignore                # Игнорируемые файлы
├── requirements.txt          # Зависимости
└── README.md                 # Документация




Полная структура проекта

antivirus-api/
├── .env                              # Конфигурация окружения
├── .gitignore                        # Игнорируемые файлы
├── alembic.ini                       # Конфигурация Alembic
├── requirements.txt                  # Зависимости Python
├── README.md                         # Документация проекта
│
├── app/                              # Основное приложение
│   ├── __init__.py                   # Инициализация пакета
│   ├── main.py                       # Точка входа FastAPI
│   │
│   ├── core/                         # Ядро системы
│   │   ├── __init__.py
│   │   ├── config.py                 # Настройки приложения
│   │   ├── database.py               # Подключение к БД
│   │   ├── security.py               # Функции безопасности
│   │   └── exceptions.py             # Кастомные исключения
│   │
│   ├── models/                       # Модели данных
│   │   ├── __init__.py
│   │   ├── base.py                   # Базовые модели
│   │   ├── user.py                   # Пользователи
│   │   ├── signature.py              # Антивирусные сигнатуры
│   │   ├── file.py                   # Файлы
│   │   ├── history.py                # История изменений
│   │   └── audit.py                  # Аудит действий
│   │
│   ├── schemas/                      # Pydantic схемы
│   │   ├── __init__.py
│   │   ├── base.py                   # Базовые схемы
│   │   ├── user.py                   # Схемы пользователей
│   │   ├── signature.py              # Схемы сигнатур
│   │   ├── file.py                   # Схемы файлов
│   │   └── token.py                  # Схемы токенов
│   │
│   ├── services/                     # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── auth.py                   # Аутентификация
│   │   ├── user.py                   # Управление пользователями
│   │   ├── signature.py              # Работа с сигнатурами
│   │   ├── scanner.py                # Сканирование файлов
│   │   ├── digital_signature.py      # ЭЦП
│   │   └── file.py                   # Управление файлами
│   │
│   ├── api/                          # API эндпоинты
│   │   ├── __init__.py
│   │   ├── dependencies.py           # Зависимости API
│   │   └── v1/                       # API версии 1
│   │       ├── __init__.py
│   │       ├── auth.py               # Аутентификация
│   │       ├── users.py              # Пользователи
│   │       ├── signatures.py         # Сигнатуры
│   │       ├── files.py              # Файлы
│   │       ├── admin.py              # Администрирование
│   │       ├── system.py             # Системные эндпоинты
│   │       ├── history.py            # История (опционально)
│   │       ├── reports.py            # Отчеты (опционально)
│   │       └── scan.py               # Сканирование (опционально)
│   │
│   ├── utils/                        # Вспомогательные утилиты
│   │   ├── __init__.py
│   │   ├── rabin_karp.py             # Алгоритм Рабина-Карпа
│   │   └── storage.py                # Работа с хранилищем
│   │
│   └── tests/                        # Тесты
│       ├── __init__.py
│       ├── conftest.py               # Фикстуры pytest
│       ├── test_services/            # Тесты сервисов
│       │   ├── test_auth_service.py
│       │   ├── test_user_service.py
│       │   ├── test_signature_service.py
│       │   └── test_file_scanner.py
│       └── test_api/                 # Тесты API
│           ├── test_auth_api.py
│           ├── test_users_api.py
│           └── test_files_api.py
│
├── migrations/                       # Миграции базы данных
│   ├── versions/                     # Файлы миграций
│   │   └── 2023_01_01_0001_initial_tables.py
│   ├── env.py                        # Конфигурация Alembic
│   └── README                        # Инструкции по миграциям
│
└── static/                           # Статические файлы
    ├── keys/                         # Ключи ЭЦП
    │   ├── private_key.pem
    │   ├── public_key.pem
    │   ├── key_management.py         # Утилиты управления ключами
    │   └── README.md                 # Инструкции по ключам
    │
    └── temp/                         # Временные файлы
        ├── uploads/                  # Загруженные файлы
        ├── scans/                    # Файлы сканирования
        ├── temp_file_manager.py      # Менеджер временных файлов
        └── README.md                 # Правила работы с temp
