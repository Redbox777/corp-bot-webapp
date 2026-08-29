"""
API Gateway - Роутинг между микросервисами + Swagger
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import time

def create_app():
    app = Flask(__name__, static_folder='../docs', static_url_path='/docs')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
    CORS(app)
    
    # Инициализация Celery
    from app.celery import celery_init_app
    celery = celery_init_app(app)
    
    # Импортируем роуты
    from app.routes.player import player_bp
    from app.routes.shop import shop_bp
    from app.routes.boss import boss_bp
    from app.routes.achievements import achievements_bp
    from app.routes.events import events_bp
    from app.routes.rebirth import rebirth_bp
    from app.routes.referrals import referrals_bp
    from app.routes.leaderboard import leaderboard_bp
    
    from services.auth import auth_bp
    from services.game import game_bp
    from services.notifications import notifications_bp
    
    # Регистрируем blueprint'ы
    app.register_blueprint(player_bp, url_prefix='/api')
    app.register_blueprint(shop_bp, url_prefix='/api')
    app.register_blueprint(boss_bp, url_prefix='/api')
    app.register_blueprint(achievements_bp, url_prefix='/api')
    app.register_blueprint(events_bp, url_prefix='/api')
    app.register_blueprint(rebirth_bp, url_prefix='/api')
    app.register_blueprint(referrals_bp, url_prefix='/api')
    app.register_blueprint(leaderboard_bp, url_prefix='/api')
    
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
    
    # Swagger UI
    @app.route('/docs')
    def swagger_ui():
        return send_from_directory(app.static_folder, 'swagger.html')
    
    # Главная страница с документацией
    @app.route('/')
    def index():
        return jsonify({
            "name": "Corp Tycoon API",
            "version": "2.1.0",
            "features": {
                "microservices": True,
                "caching": True,
                "celery": True,
                "rate_limiting": True,
                "swagger_docs": True
            },
            "endpoints": {
                "health": "/health",
                "stats": "/api/stats",
                "swagger": "/docs",
                "openapi_spec": "/docs/openapi.yaml",
                "player": "/api/player/<chat_id>",
                "click": "POST /api/click/<chat_id>",
                "shop": "/api/shop",
                "buy": "POST /api/buy/<chat_id>/<upgrade_id>",
                "boss": "/api/boss_status",
                "achievements": "/api/achievements"
            },
            "documentation": {
                "swagger_ui": "http://localhost:5000/docs",
                "github": "https://github.com/Redbox777/corp-bot-webapp"
            }
        })
    
    return app

# Endpoint для просмотра логов (только для админа!)
@app.route('/admin/logs')
def view_logs():
    """Просмотр последних логов (защитить паролем!)"""
    import os
    
    # Простая защита паролем
    password = request.args.get('password')
    if password != os.environ.get('ADMIN_PASSWORD', 'admin123'):
        return jsonify({"error": "Unauthorized"}), 401
    
    # Читаем последние ошибки
    try:
        with open('logs/errors_' + datetime.now().strftime("%Y%m") + '.log', 'r') as f:
            lines = f.readlines()[-50:]  # Последние 50 строк
        return jsonify({
            "logs": ''.join(lines),
            "timestamp": datetime.now().isoformat()
        })
    except FileNotFoundError:
        return jsonify({"logs": "No errors yet", "timestamp": datetime.now().isoformat()})

@app.route('/admin/bugs')
def view_bugs():
    """Просмотр багов"""
    import os
    
    password = request.args.get('password')
    if password != os.environ.get('ADMIN_PASSWORD', 'admin123'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        bugs = []
        with open('logs/bugs.jsonl', 'r') as f:
            for line in f.readlines()[-20:]:  # Последние 20 багов
                bugs.append(json.loads(line))
        return jsonify({"bugs": bugs})
    except FileNotFoundError:
        return jsonify({"bugs": [], "message": "No bugs recorded yet"})
