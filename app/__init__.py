from flask import Flask, jsonify
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
    CORS(app)
    
    # Импортируем все blueprint'ы
    from app.routes.player import player_bp
    from app.routes.shop import shop_bp
    from app.routes.boss import boss_bp
    from app.routes.achievements import achievements_bp
    from app.routes.events import events_bp
    from app.routes.rebirth import rebirth_bp
    from app.routes.referrals import referrals_bp
    from app.routes.leaderboard import leaderboard_bp
    
    # Регистрируем
    app.register_blueprint(player_bp, url_prefix='/api')
    app.register_blueprint(shop_bp, url_prefix='/api')
    app.register_blueprint(boss_bp, url_prefix='/api')
    app.register_blueprint(achievements_bp, url_prefix='/api')
    app.register_blueprint(events_bp, url_prefix='/api')
    app.register_blueprint(rebirth_bp, url_prefix='/api')
    app.register_blueprint(referrals_bp, url_prefix='/api')
    app.register_blueprint(leaderboard_bp, url_prefix='/api')
    
    # Health check
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'version': '1.0.0'})
    
    return app
