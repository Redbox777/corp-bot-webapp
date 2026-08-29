"""
API Gateway - Роутинг между микросервисами + Celery
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import time

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
    CORS(app)
    
    # Инициализация Celery
    from app.celery import celery_init_app
    celery = celery_init_app(app)
    
    # Импортируем старые роуты
    from app.routes.player import player_bp
    from app.routes.shop import shop_bp
    from app.routes.boss import boss_bp
    from app.routes.achievements import achievements_bp
    from app.routes.events import events_bp
    from app.routes.rebirth import rebirth_bp
    from app.routes.referrals import referrals_bp
    from app.routes.leaderboard import leaderboard_bp
    
    # Импортируем микросервисы
    from services.auth import auth_bp
    from services.game import game_bp
    from services.notifications import notifications_bp
    
    # Регистрируем старые роуты
    app.register_blueprint(player_bp, url_prefix='/api')
    app.register_blueprint(shop_bp, url_prefix='/api')
    app.register_blueprint(boss_bp, url_prefix='/api')
    app.register_blueprint(achievements_bp, url_prefix='/api')
    app.register_blueprint(events_bp, url_prefix='/api')
    app.register_blueprint(rebirth_bp, url_prefix='/api')
    app.register_blueprint(referrals_bp, url_prefix='/api')
    app.register_blueprint(leaderboard_bp, url_prefix='/api')
    
    # Регистрируем микросервисы
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(notifications_bp)
    
    # Health check
    @app.route('/health')
    def health():
        return jsonify({
            "status": "ok",
            "version": "2.1.0",
            "architecture": "microservices",
            "celery": "active",
            "services": {
                "auth": "active",
                "game": "active",
                "notifications": "active"
            },
            "timestamp": time.time()
        })
    
    # Статистика
    @app.route('/api/stats')
    def all_stats():
        from app.utils.cache import get_cache_stats
        
        return jsonify({
            "cache": get_cache_stats(),
            "celery": {
                "status": "active",
                "broker": app.config.get('CELERY_BROKER_URL', 'unknown')
            },
            "timestamp": time.time()
        })
    
    # === CELERY API ENDPOINTS ===
    
    @app.route('/api/celery/send-notification', methods=['POST'])
    def api_send_notification():
        """Отправить уведомление через Celery"""
        from app.tasks import send_notification_task
        
        data = request.get_json() or {}
        chat_id = data.get('chat_id', 'test_user')
        message = data.get('message', 'Test notification')
        notif_type = data.get('type', 'info')
        
        # Асинхронная отправка
        task = send_notification_task.delay(chat_id, message, notif_type)
        
        return jsonify({
            "success": True,
            "task_id": task.id,
            "message": "Notification queued",
            "status_url": f"/api/celery/task-status/{task.id}"
        })
    
    @app.route('/api/celery/batch-clicks/<chat_id>', methods=['POST'])
    def api_batch_clicks(chat_id):
        """Обработать пакет кликов"""
        from app.tasks import process_batch_clicks
        
        data = request.get_json() or {}
        clicks = data.get('count', 10)
        
        task = process_batch_clicks.delay(chat_id, clicks)
        
        return jsonify({
            "success": True,
            "task_id": task.id,
            "message": f"Processing {clicks} clicks",
            "status_url": f"/api/celery/task-status/{task.id}"
        })
    
    @app.route('/api/celery/task-status/<task_id>', methods=['GET'])
    def api_task_status(task_id):
        """Получить статус задачи"""
        from celery.result import AsyncResult
        
        task_result = AsyncResult(task_id)
        
        return jsonify({
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None,
            "ready": task_result.ready()
        })
    
    @app.route('/api/celery/heavy-task', methods=['POST'])
    def api_heavy_task():
        """Запустить тяжёлую задачу"""
        from app.tasks import heavy_computation_task
        
        data = request.get_json() or {}
        size = data.get('size', 1000)
        
        task = heavy_computation_task.delay(size)
        
        return jsonify({
            "success": True,
            "task_id": task.id,
            "message": f"Processing {size} items",
            "status_url": f"/api/celery/task-status/{task.id}"
        })
    
    # Главная страница
    @app.route('/')
    def index():
        return jsonify({
            "name": "Corp Tycoon API",
            "version": "2.1.0",
            "features": {
                "microservices": True,
                "caching": True,
                "celery": True,
                "rate_limiting": True
            },
            "endpoints": {
                "health": "/health",
                "stats": "/api/stats",
                "celery": {
                    "send_notification": "POST /api/celery/send-notification",
                    "batch_clicks": "POST /api/celery/batch-clicks/<chat_id>",
                    "heavy_task": "POST /api/celery/heavy-task",
                    "task_status": "GET /api/celery/task-status/<task_id>"
                }
            }
        })
    
    return app
