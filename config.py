import os

class Config:
    DATABASE_PATH = 'players.db'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    APP_URL = os.environ.get('APP_URL', 'https://corp-bot-webapp.onrender.com')
    BOT_USERNAME = os.environ.get('BOT_USERNAME', 'MagnatZeroBot')
    
    # Игровые константы
    REFERRAL_BONUS = 500
    REFERRAL_PERCENT = 0.01
    REBIRTH_THRESHOLD_LEVEL = 5
    REBIRTH_THRESHOLD_EARNED = 5000
    PRESTIGE_MULTIPLIER = 0.05  # +5% за кристалл
    
    # Улучшения
    UPGRADES = {
        "shawarma": {"name": "Ларёк", "cost": 100, "income": 2, "icon": "", "type": "passive"},
        "coffee": {"name": "Кофе", "cost": 500, "income": 10, "icon": "☕", "type": "passive"},
        "office": {"name": "Офис", "cost": 2000, "income": 50, "icon": "", "type": "passive"},
        "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "🏭", "type": "passive"},
        "bank": {"name": "Банк", "cost": 50000, "income": 1500, "icon": "🏦", "type": "passive"},
        "mouse": {"name": "Золотая мышь", "cost": 200, "power": 5, "icon": "🖱️", "type": "click"},
        "ai_bot": {"name": "AI-Бот", "cost": 1000, "power": 25, "icon": "🤖", "type": "click"},
        "quantum": {"name": "Квантовый ПК", "cost": 100000, "power": 500, "icon": "💻", "type": "click"}
    }
    
    # Квесты
    QUESTS = [
        {"id": "click_100", "name": "Кликер", "desc": "Сделай 100 кликов", "target": 100, "type": "clicks", "reward": 200, "daily": True},
        {"id": "earn_1000", "name": "Магнат", "desc": "Заработай 1000$", "target": 1000, "type": "total_earned", "reward": 500, "daily": True},
        {"id": "rebirth_1", "name": "Новая жизнь", "desc": "Переродись 1 раз", "target": 1, "type": "prestiges", "reward": 1000, "daily": False}
    ]

config = Config()
