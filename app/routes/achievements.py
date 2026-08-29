from flask import Blueprint, jsonify

achievements_bp = Blueprint('achievements', __name__)

ACHIEVEMENTS = [
    {"id": "click_10", "name": "Первый шаг", "desc": "10 кликов", "target": 10, "type": "clicks", "reward": 50, "rarity": "common"},
    {"id": "click_100", "name": "Кликер", "desc": "100 кликов", "target": 100, "type": "clicks", "reward": 200, "rarity": "common"},
    {"id": "click_1000", "name": "Тап-мастер", "desc": "1000 кликов", "target": 1000, "type": "clicks", "reward": 1000, "rarity": "uncommon"},
    {"id": "earn_100", "name": "Старт", "desc": "100$ всего", "target": 100, "type": "total_earned", "reward": 100, "rarity": "common"},
    {"id": "earn_1000", "name": "Магнат", "desc": "1000$ всего", "target": 1000, "type": "total_earned", "reward": 500, "rarity": "common"},
    {"id": "earn_10000", "name": "Богач", "desc": "10000$ всего", "target": 10000, "type": "total_earned", "reward": 2500, "rarity": "uncommon"},
    {"id": "first_business", "name": "Предприниматель", "desc": "Первый бизнес", "target": 1, "type": "upgrades_count", "reward": 100, "rarity": "common"},
    {"id": "ten_upgrades", "name": "Инвестор", "desc": "10 улучшений", "target": 10, "type": "upgrades_count", "reward": 500, "rarity": "uncommon"},
    {"id": "rebirth_1", "name": "Новая жизнь", "desc": "1 перерождение", "target": 1, "type": "prestiges", "reward": 1000, "rarity": "rare"}
]

@achievements_bp.route('/achievements', methods=['GET'])
def get_achievements():
    """Получить список достижений"""
    return jsonify(ACHIEVEMENTS)
