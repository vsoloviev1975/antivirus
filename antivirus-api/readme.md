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

