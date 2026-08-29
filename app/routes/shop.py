from flask import Blueprint, jsonify, request
from app.database import get_db
from app.logger import log_errors, log_bug, setup_logger
import json
import time

shop_bp = Blueprint('shop', __name__)

logger = setup_logger()

UPGRADES = {
    "shawarma": {"name": "Ларёк", "cost": 100, "income": 2, "icon": "", "type": "passive"},
    "coffee": {"name": "Кофе", "cost": 500, "income": 10, "icon": "☕", "type": "passive"},
    "pizza": {"name": "Пиццерия", "cost": 1500, "income": 25, "icon": "🍕", "type": "passive"},
    "office": {"name": "Офис", "cost": 3000, "income": 60, "icon": "", "type": "passive"},
    "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "🏭", "type": "passive"},
    "taxi": {"name": "Такси", "cost": 20000, "income": 450, "icon": "🚕", "type": "passive"},
    "bank": {"name": "Банк", "cost": 80000, "income": 1500, "icon": "🏦", "type": "passive"},
    "mall": {"name": "ТЦ", "cost": 150000, "income": 3000, "icon": "🛍️", "type": "passive"},
    "tech_park": {"name": "IT Парк", "cost": 500000, "income": 8000, "icon": "", "type": "passive"},
    "spaceport": {"name": "Космопорт", "cost": 2000000, "income": 25000, "icon": "🚀", "type": "passive"},
    "mouse": {"name": "Золотая мышь", "cost": 200, "power": 5, "icon": "🖱️", "type": "click"},
    "ai_bot": {"name": "AI-Бот", "cost": 1000, "power": 25, "icon": "", "type": "click"},
    "exosuit": {"name": "Экзоскелет", "cost": 5000, "power": 100, "icon": "💪", "type": "click"},
    "quantum": {"name": "Квантовый палец", "cost": 50000, "power": 500, "icon": "⚡", "type": "click"}
}

@shop_bp.route('/shop', methods=['GET'])
def get_shop():
    """Получить список улучшений"""
    logger.debug("Shop endpoint called")
    return jsonify(UPGRADES)

@shop_bp.route('/buy/<chat_id>/<upgrade_id>', methods=['POST'])
@log_errors  # Автоматическое логирование ошибок
def buy_upgrade(chat_id, upgrade_id):
    """Купить улучшение (с подробным логированием)"""
    logger.info(f"Purchase attempt: {chat_id} wants to buy {upgrade_id}")
    
    if upgrade_id not in UPGRADES:
        logger.warning(f"Invalid upgrade: {upgrade_id}")
        return jsonify({"error": "Invalid upgrade"}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Получаем текущее состояние
        c.execute('SELECT balance, upgrades FROM players WHERE chat_id = ?', (chat_id,))
        row = c.fetchone()
        
        if not row:
            logger.error(f"Player not found: {chat_id}")
            return jsonify({"error": "Player not found"}), 404
        
        p = dict(row)
        p["upgrades"] = json.loads(p["upgrades"] or "{}")
        
        u = UPGRADES[upgrade_id]
        cnt = p["upgrades"].get(upgrade_id, 0)
        price = int(u["cost"] * (1.15 ** cnt))
        bal = p["balance"] or 0
        
        logger.info(f"Purchase details: balance={bal}, price={price}, can_afford={bal >= price}")
        
        if bal < price:
            logger.warning(f"Insufficient funds: {chat_id} has {bal}, needs {price}")
            return jsonify({"error": "Мало денег"}), 400
        
        # Выполняем покупку
        nb = bal - price
        nu = {**p["upgrades"], upgrade_id: cnt + 1}
        
        c.execute('UPDATE players SET balance=?, upgrades=?, last_update=? WHERE chat_id=?',
                 (nb, json.dumps(nu), time.time(), chat_id))
        conn.commit()
        
        # ВАЖНО: Перечитываем данные чтобы убедиться что сохранилось
        c.execute('SELECT balance, upgrades FROM players WHERE chat_id = ?', (chat_id,))
        verify_row = c.fetchone()
        verify_data = dict(verify_row) if verify_row else {}
        verify_upgrades = json.loads(verify_data.get("upgrades") or "{}")
        
        logger.info(f"Purchase successful: new_balance={nb}, upgrade_count={verify_upgrades.get(upgrade_id, 0)}")
        
        # Проверяем что улучшение действительно сохранилось
        if verify_upgrades.get(upgrade_id, 0) != cnt + 1:
            logger.error(f"DATA INCONSISTENCY: Expected {cnt + 1}, got {verify_upgrades.get(upgrade_id, 0)}")
            log_bug(
                endpoint="buy_upgrade",
                user_id=chat_id,
                error="Upgrade not saved correctly",
                data={
                    "upgrade_id": upgrade_id,
                    "expected_count": cnt + 1,
                    "actual_count": verify_upgrades.get(upgrade_id, 0),
                    "balance_before": bal,
                    "balance_after": nb
                }
            )
        
        conn.close()
        
        return jsonify({
            "balance": nb,
            "upgrades": nu,
            "success": True,
            "message": f"Куплено: {u['name']}"
        })
        
    except Exception as e:
        logger.error(f"Purchase failed: {str(e)}", exc_info=True)
        conn.rollback()
        conn.close()
        raise  # Декоратор @log_errors обработает
