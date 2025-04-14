"""
frontend/app.py
Основной модуль фронтенд-приложения для Antivirus File Storage API

Реализует:
- Взаимодействие с FastAPI бэкендом через REST
- Веб-интерфейс на Flask + Bootstrap
- Загрузку/удаление/сканирование файлов
- Управление антивирусными сигнатурами
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import uuid
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from werkzeug.utils import secure_filename
import os

# Инициализация Flask приложения
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Для flash-сообщений и сессий

"""
КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ
"""
# Настройки подключения к бэкенду (должны совпадать с main.py)
BACKEND_URL = "http://localhost:8000"  # URL FastAPI сервера

# Настройка системы логирования (аналогично бэкенду)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создание директории для логов
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Обработчик с ротацией логов
file_handler = RotatingFileHandler(
    'logs/frontend.log',
    maxBytes=1024*1024,  # 1 MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logger.addHandler(file_handler)
logger.addHandler(logging.StreamHandler())

# Конфигурация папки для временных загрузок
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

"""
РОУТИНГ И КОНТРОЛЛЕРЫ
"""

@app.route('/')
def index():
    """
    Главная страница приложения
    Показывает:
    - Форму загрузки файлов
    - Список всех загруженных файлов
    - Кнопки действий для каждого файла
    """
    try:
        logger.info("Обработка запроса главной страницы")
        
        # Запрос к бэкенду для получения списка файлов
        response = requests.get(f"{BACKEND_URL}/allfiles")
        
        if response.status_code != 200:
            logger.error(f"Ошибка API бэкенда: {response.status_code}")
            flash("Ошибка при получении списка файлов", "danger")
            files = []
        else:
            files = response.json()
            logger.info(f"Успешно получено файлов: {len(files)}")
        
        return render_template('index.html', files=files)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Сетевая ошибка: {str(e)}")
        flash("Ошибка подключения к серверу", "danger")
        return render_template('index.html', files=[])
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}")
        flash("Внутренняя ошибка сервера", "danger")
        return render_template('index.html', files=[])

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Обработчик загрузки файла
    Действия:
    1. Сохраняет файл во временную папку
    2. Отправляет в бэкенд через API
    3. Удаляет временный файл
    4. Возвращает статус операции
    """
    try:
        logger.info("Начало обработки загрузки файла")
        
        # Валидация наличия файла в запросе
        if 'file' not in request.files:
            logger.warning("Отсутствует файл в запросе")
            flash("Файл не был выбран", "warning")
            return redirect(url_for('index'))
        
        file = request.files['file']
        
        # Валидация имени файла
        if file.filename == '':
            logger.warning("Пустое имя файла")
            flash("Не выбрано имя файла", "warning")
            return redirect(url_for('index'))
        
        if file:
            # Безопасное сохранение временного файла
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            logger.info(f"Временный файл сохранен: {temp_path}")
            
            try:
                # Отправка файла в бэкенд
                with open(temp_path, 'rb') as f:
                    files = {'file': (filename, f)}
                    response = requests.post(
                        f"{BACKEND_URL}/files/upload",
                        files=files
                    )
                
                # Обработка ответа от бэкенда
                if response.status_code == 200:
                    file_id = response.json().get('file_id')
                    logger.info(f"Файл загружен. ID: {file_id}")
                    flash("Файл успешно загружен", "success")
                else:
                    logger.error(f"Ошибка бэкенда: {response.status_code}")
                    flash("Ошибка при загрузке файла", "danger")
            
            finally:
                # Гарантированное удаление временного файла
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.debug("Временный файл удален")
        
        return redirect(url_for('index'))
    
    except Exception as e:
        logger.critical(f"Ошибка загрузки: {str(e)}")
        flash("Внутренняя ошибка сервера", "danger")
        return redirect(url_for('index'))

@app.route('/file/<file_id>')
def view_file(file_id):
    """
    Просмотр детальной информации о файле
    Включает:
    - Основные метаданные
    - Результаты сканирования (если есть)
    """
    try:
        logger.info(f"Запрос информации о файле: {file_id}")
        
        # Валидация UUID
        try:
            uuid.UUID(file_id)
        except ValueError:
            logger.error(f"Невалидный UUID: {file_id}")
            flash("Неверный идентификатор файла", "danger")
            return redirect(url_for('index'))
        
        # Запрос к бэкенду
        response = requests.get(f"{BACKEND_URL}/files/{file_id}")
        
        if response.status_code == 404:
            logger.warning(f"Файл не найден: {file_id}")
            flash("Файл не найден", "warning")
            return redirect(url_for('index'))
        elif response.status_code != 200:
            logger.error(f"Ошибка API: {response.status_code}")
            flash("Ошибка при получении данных", "danger")
            return redirect(url_for('index'))
        
        file_info = response.json()
        logger.info(f"Получены данные файла: {file_info.get('name')}")
        
        return render_template('file_detail.html', file=file_info)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети: {str(e)}")
        flash("Ошибка подключения", "danger")
        return redirect(url_for('index'))
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}")
        flash("Внутренняя ошибка", "danger")
        return redirect(url_for('index'))

@app.route('/delete/<file_id>')
def delete_file(file_id):
    """
    Удаление файла по ID
    """
    try:
        logger.info(f"Запрос удаления файла: {file_id}")
        
        # Валидация UUID
        try:
            uuid.UUID(file_id)
        except ValueError:
            logger.error(f"Невалидный UUID: {file_id}")
            flash("Неверный ID файла", "danger")
            return redirect(url_for('index'))
        
        # Запрос на удаление
        response = requests.delete(f"{BACKEND_URL}/files/{file_id}")
        
        if response.status_code == 200:
            deleted_id = response.json().get('deleted_file_id')
            if deleted_id == "File not found for deletion.":
                logger.warning(f"Файл не найден: {file_id}")
                flash("Файл не найден", "warning")
            else:
                logger.info(f"Файл удален: {deleted_id}")
                flash("Файл удален", "success")
        else:
            logger.error(f"Ошибка API: {response.status_code}")
            flash("Ошибка удаления", "danger")
        
        return redirect(url_for('index'))
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети: {str(e)}")
        flash("Ошибка подключения", "danger")
        return redirect(url_for('index'))
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}")
        flash("Внутренняя ошибка", "danger")
        return redirect(url_for('index'))

@app.route('/scan/<file_id>')
def scan_file(file_id):
    """
    Инициация сканирования файла
    Возвращает страницу с результатами
    """
    try:
        logger.info(f"Запрос сканирования файла: {file_id}")
        
        # Валидация UUID
        try:
            uuid.UUID(file_id)
        except ValueError:
            logger.error(f"Невалидный UUID: {file_id}")
            flash("Неверный ID файла", "danger")
            return redirect(url_for('index'))
        
        # Запрос на сканирование
        response = requests.post(
            f"{BACKEND_URL}/files/scan",
            params={"file_id": file_id}
        )
        
        if response.status_code == 200:
            scan_result = response.json()
            logger.info(f"Сканирование завершено: {file_id}")
            return render_template('scan_result.html', 
                                 file_id=file_id, 
                                 result=scan_result)
        elif response.status_code == 404:
            logger.warning(f"Файл не найден: {file_id}")
            flash("Файл не найден", "warning")
        else:
            logger.error(f"Ошибка API: {response.status_code}")
            flash("Ошибка сканирования", "danger")
        
        return redirect(url_for('view_file', file_id=file_id))
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети: {str(e)}")
        flash("Ошибка подключения", "danger")
        return redirect(url_for('index'))
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}")
        flash("Внутренняя ошибка", "danger")
        return redirect(url_for('index'))

@app.route('/signatures')
def list_signatures():
    """
    Страница управления антивирусными сигнатурами
    Показывает:
    - Таблицу всех сигнатур
    - Кнопки управления
    """
    try:
        logger.info("Запрос списка сигнатур")
        
        response = requests.get(f"{BACKEND_URL}/signatures")
        
        if response.status_code != 200:
            logger.error(f"Ошибка API: {response.status_code}")
            flash("Ошибка получения сигнатур", "danger")
            signatures = []
        else:
            signatures = response.json()
            logger.info(f"Получено сигнатур: {len(signatures)}")
        
        return render_template('signatures.html', signatures=signatures)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети: {str(e)}")
        flash("Ошибка подключения", "danger")
        return render_template('signatures.html', signatures=[])
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}")
        flash("Внутренняя ошибка", "danger")
        return render_template('signatures.html', signatures=[])

@app.route('/signature/manage', methods=['GET', 'POST'])
def manage_signature():
    """
    Форма управления сигнатурой (CRUD)
    Обрабатывает:
    - Создание новой сигнатуры
    - Редактирование существующей
    """
    try:
        if request.method == 'GET':
            # Показ формы для новой/редактируемой сигнатуры
            return render_template('manage_signature.html', json=[])
        
        # Обработка данных формы
        logger.info("Обработка данных сигнатуры")
        
        # Сбор данных из формы
        signature_data = {
            'threat_name': request.form.get('threat_name'),
            'first_bytes': request.form.get('first_bytes'),
            'remainder_hash': request.form.get('remainder_hash'),
            'remainder_length': request.form.get('remainder_length'),
            'file_type': request.form.get('file_type'),
            'offset_start': request.form.get('offset_start'),
            'offset_end': request.form.get('offset_end'),
            'status': request.form.get('status', 'ACTUAL')
        }
        
        # Добавление ID для редактирования
        signature_id = request.form.get('id')
        if signature_id:
            signature_data['id'] = signature_id
        
        # Отправка данных в бэкенд
        response = requests.post(
            f"{BACKEND_URL}/signatures/manage",
            json=signature_data
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Сигнатура сохранена. ID: {result.get('signature_id')}")
            flash("Сигнатура сохранена", "success")
        else:
            logger.error(f"Ошибка API: {response.status_code}")
            flash("Ошибка сохранения", "danger")
        
        return redirect(url_for('list_signatures'))
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети: {str(e)}")
        flash("Ошибка подключения", "danger")
        return redirect(url_for('list_signatures'))
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}")
        flash("Внутренняя ошибка", "danger")
        return redirect(url_for('list_signatures'))
        
@app.route('/history')
def history():
    """
    Отображение страницы истории изменений сигнатур
    Параметры запроса:
    - signature_id: фильтр по ID сигнатуры (опционально)
    - limit: ограничение количества записей (по умолчанию 100)
    """
    try:
        logger.info("Запрос истории изменений")
        
        # Получаем параметры фильтрации из запроса
        signature_id = request.args.get('signature_id')
        limit = request.args.get('limit', default=100, type=int)
        
        # Параметры для API бэкенда
        params = {'limit': limit}
        if signature_id:
            params['signature_id'] = signature_id
        
        # Запрос к бэкенду
        response = requests.get(f"{BACKEND_URL}/history", params=params)
        
        if response.status_code != 200:
            logger.error(f"Ошибка API истории: {response.status_code}")
            flash("Ошибка получения истории изменений", "danger")
            history = []
        else:
            history = response.json()
            #logger.info(f"Получено записей истории: {len(history)}")
            print(history)
        
        return render_template('history.html', 
                            history=history,
                            signature_id=signature_id,
                            limit=limit)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети: {str(e)}")
        flash("Ошибка подключения", "danger")
        return render_template('history.html', history=[])
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}")
        flash("Внутренняя ошибка", "danger")
        return render_template('history.html', history=[])

@app.route('/audit')
def audit():
    """
    Отображение журнала аудита
    Параметры запроса:
    - entity_type: фильтр по типу сущности (опционально)
    - operation_type: фильтр по типу операции (CREATED/UPDATED/DELETED)
    - limit: ограничение количества записей (по умолчанию 100)
    """
    try:
        logger.info("Запрос журнала аудита")
        
        # Получаем параметры фильтрации из запроса
        entity_type = request.args.get('entity_type')
        operation_type = request.args.get('operation_type')
        limit = request.args.get('limit', default=100, type=int)
        
        # Параметры для API бэкенда
        params = {
            'limit': limit,
            'entity_type': entity_type,
            'operation_type': operation_type
        }
        
        # Запрос к бэкенду
        response = requests.get(f"{BACKEND_URL}/audit", params=params)
        
        if response.status_code != 200:
            logger.error(f"Ошибка API аудита: {response.status_code}")
            flash("Ошибка получения журнала аудита", "danger")
            audit_logs = []
        else:
            audit_logs = response.json()
            logger.info(f"Получено записей аудита: {len(audit_logs)}")
        
        return render_template('audit.html',
                            audit_logs=audit_logs,
                            entity_type=entity_type,
                            operation_type=operation_type,
                            limit=limit)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети: {str(e)}")
        flash("Ошибка подключения", "danger")
        return render_template('audit.html', audit_logs=[])
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}")
        flash("Внутренняя ошибка", "danger")
        return render_template('audit.html', audit_logs=[])        

if __name__ == '__main__':
    # Запуск Flask-приложения
    app.run(host='0.0.0.0', port=5000, debug=True)
