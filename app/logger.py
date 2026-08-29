"""
Профессиональная система логирования
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json

class CustomFormatter(logging.Formatter):
    """Красивый форматер с цветами (для консоли)"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[34;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    format_str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s "
        "[%(filename)s:%(lineno)d]"
    )
    
    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: blue + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(name='corp_bot'):
    """Настроить логгер"""
    
    # Создаём папку для логов
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Основной логгер
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Если уже есть хендлеры — не добавляем повторно
    if logger.handlers:
        return logger
    
    # 1. Файловый хендлер (все логи)
    file_handler = RotatingFileHandler(
        f'{log_dir}/app_{datetime.now().strftime("%Y%m")}.log',
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]'
    )
    file_handler.setFormatter(file_formatter)
    
    # 2. Файловый хендлер (только ошибки)
    error_handler = RotatingFileHandler(
        f'{log_dir}/errors_{datetime.now().strftime("%Y%m")}.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # 3. Консольный хендлер (с цветами)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CustomFormatter())
    
    # Добавляем хендлеры
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

# Специальный логгер для багов
def log_bug(endpoint: str, user_id: str, error: str, data: dict = None):
    """
    Логирование багов в отдельный файл
    """
    logger = setup_logger()
    
    bug_report = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "user_id": user_id,
        "error": error,
        "data": data or {}
    }
    
    # Пишем в отдельный JSON файл для удобства анализа
    with open('logs/bugs.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(bug_report, ensure_ascii=False) + '\n')
    
    logger.error(f" BUG REPORT: {json.dumps(bug_report, ensure_ascii=False)}")
    
    return bug_report

# Декоратор для логирования ошибок
def log_errors(func):
    """Декоратор для автоматического логирования ошибок в endpoint'ах"""
    from functools import wraps
    from flask import request, jsonify
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = setup_logger()
        start_time = datetime.now()
        
        try:
            logger.info(f"Request: {request.method} {request.path}")
            result = func(*args, **kwargs)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Response: {request.method} {request.path} - {duration:.3f}s")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in {request.path} after {duration:.3f}s: {str(e)}", exc_info=True)
            
            # Логируем баг
            log_bug(
                endpoint=f"{request.method} {request.path}",
                user_id=request.view_args.get('chat_id', 'unknown'),
                error=str(e),
                data=dict(request.args) if request.args else {}
            )
            
            return jsonify({
                "error": "Internal server error",
                "message": str(e) if os.environ.get('FLASK_ENV') == 'development' else "Something went wrong"
            }), 500
    
    return wrapper
