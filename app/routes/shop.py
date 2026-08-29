from flask import Blueprint, jsonify, request
from app.database import get_db
import json
import time

shop_bp = Blueprint('shop', __name__)

UPGRADES = {
    "shawarma": {"name": "Ларёк", "cost": 100, "income": 2, "icon": "🌯", "type": "passive"},
    "coffee": {"name": "Кофе", "cost": 500, "income": 10, "icon": "☕", "type": "passive"},
    "pizza": {"name": "Пиццерия", "cost": 1500, "income": 25, "icon": "🍕", "type": "passive"},
    "office": {"name": "Офис", "cost": 3000, "income": 60, "icon": "🏢", "type": "passive"},
    "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "🏭", "type": "passive"},
    "taxi": {"name": "Такси", "cost": 20000, "income": 450, "icon": "", "type": "passive"},
    "bank": {"name": "Банк", "cost": 80000, "income": 1500, "icon": "🏦", "type": "passive"},
    "mall": {"name": "ТЦ", "cost": 150000, "income": 3000, "icon": "🛍️", "type": "passive"},
    "tech_park": {"name": "IT Парк", "cost": 500000, "income": 8000, "icon": "💻", "type": "passive"},
    "spaceport": {"name": "Космопорт", "cost": 2000000, "income": 25000, "icon": "🚀", "type": "passive"},
    "mouse": {"name": "Золотая мышь", "cost": 200, "power": 5, "icon": "️", "type": "click"},
    "ai_bot": {"name": "AI-Бот", "cost": 1000, "power": 25, "icon": "🤖", "type": "click"},
    "exosuit": {"name": "Экзоскелет", "cost": 5000, "power": 100, "icon": "💪", "type": "click"},
    "quantum": {"name": "Квантовый палец", "cost": 50000, "power": 500, "icon": "", "type": "click"}
}

@shop_bp.route('/shop', methods=['GET'])
def get_shop():
    """Получить список улучшений"""
    return jsonify(UPGRADES)

@shop_bp.route('/buy/<chat_id>/<upgrade_id>', methods=['POST'])
def buy_upgrade(chat_id, upgrade_id):
    """Купить улучшение"""
    if upgrade_id not in UPGRADES:
        return jsonify({"error": "Invalid upgrade"}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT balance, upgrades, click_power, passive_income FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"error": "Player not found"}), 404
    
    p = dict(row)
    p["upgrades"] = json.loads(p["upgrades"] or "{}")
    
    u = UPGRADES[upgrade_id]
    cnt = p["upgrades"].get(upgrade_id, 0)
    price = int(u["cost"] * (1.15 ** cnt))
    bal = p["balance"] or 0
    
    if bal < price:
        conn.close()
        return jsonify({"error": "Мало денег"}), 400
    
    nb = bal - price
    nu = {**p["upgrades"], upgrade_id: cnt + 1}
    npwr = (p["click_power"] or 10) + (u.get("power", 0) if u["type"] == "click" else 0)
    npass = (p["passive_income"] or 0) + (u.get("income", 0) if u["type"] == "passive" else 0)
    
    c.execute('UPDATE players SET balance=?, upgrades=?, click_power=?, passive_income=?, last_update=? WHERE chat_id=?',
              (nb, json.dumps(nu), npwr, npass, time.time(), chat_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        "balance": nb,
        "click_power": npwr,
        "passive_income": npass,
        "upgrades": nu,
        "success": True
    })
