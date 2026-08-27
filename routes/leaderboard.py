from flask import Blueprint, jsonify
from database import get_connection

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('/api/leaderboard', methods=['GET'])
def get_leaderboard_api():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT chat_id, balance, level FROM players ORDER BY balance DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    
    return jsonify([
        {"rank": i+1, "chat_id": r["chat_id"], "balance": r["balance"], "level": r["level"]}
        for i, r in enumerate(rows)
    ])
