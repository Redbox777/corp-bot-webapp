"""
Celery Configuration - Фоновые задачи (Termux-compatible)
"""
import os
from celery import Celery
from flask import Flask

# Явно указываем файловый брокер (без RabbitMQ/Redis)
broker_url = os.environ.get('CELERY_BROKER_URL', 'filesystem:///tmp/celery')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'cache+memory://')

celery = Celery('app', broker=broker_url, backend=result_backend)
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_pool='solo',
    broker_pool_limit=None,
    # Настройки для файлового брокера
    broker_transport_options={
        'data_folder_in': '/tmp/celery/data',
        'data_folder_out': '/tmp/celery/data',
        'polling_interval': 0.1,
    },
    # Для тестов можно поставить True (задачи выполнятся синхронно)
    task_always_eager=False,
)

def celery_init_app(app: Flask) -> Celery:
    """Интеграция Celery с Flask контекстом"""
    class FlaskTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = FlaskTask
    celery.conf.update(app.config)
    return celery
