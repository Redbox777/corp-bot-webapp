from flask import Blueprint, jsonify
from app.database import get_db
import time

rebirth_bp = Blueprint('rebirth', __name__)

@rebirth_bp.route('/rebirth/<chat_id>', methods=['POST'])
def rebirth(chat_id):
    """Перерождение игрока"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT balance, total_earned, level, prestige_points, prestige_mult, total_prestiges FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"error": "Player not found"}), 404
    
    rd = dict(row)
    lvl = rd.get("level") or 1
    te = rd.get("total_earned") or 0
    
    if lvl < 5 and te < 5000:
        conn.close()
        return jsonify({"error": f"Нужен 5 ур. или 5000$ (сейчас: {lvl}/{te})"}), 400
    
    pp = rd.get("prestige_points") or 0
    gems = max(1, (te // 5000) - pp)
    ng = pp + gems
    nm = 1.0 + (ng * 0.05)
    np = (rd.get("total_prestiges") or 0) + 1
    
    c.execute('''UPDATE players SET balance=0, clicks=0, level=1, passive_income=0, click_power=10, upgrades='{}',
        total_earned=0, last_update=?, prestige_points=?, prestige_mult=?, total_prestiges=? WHERE chat_id=?''',
        (time.time(), ng, nm, np, chat_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "gems_added": gems,
        "total_gems": ng,
        "multiplier": nm,
        "message": f"+{gems} 💎"
    })
