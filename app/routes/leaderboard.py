from flask import Blueprint, jsonify
from app.database import get_db

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    """Получить таблицу лидеров"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT chat_id, balance, level FROM players ORDER BY balance DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    
    return jsonify([
        {"rank": i+1, "chat_id": r["chat_id"], "balance": r["balance"], "level": r["level"]}
        for i, r in enumerate(rows)
    ])
