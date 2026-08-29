from flask import Blueprint, jsonify
from app.database import get_db

boss_bp = Blueprint('boss', __name__)

@boss_bp.route('/boss_status', methods=['GET'])
def boss_status():
    """Получить статус босса"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT hp, max_hp, level, name FROM boss WHERE id = 1")
    row = c.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            "hp": row["hp"],
            "max_hp": row["max_hp"],
            "level": row["level"],
            "name": row["name"]
        })
    return jsonify({"error": "No boss"}), 404
