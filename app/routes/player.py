from flask import Blueprint, jsonify, request
from app.database import get_db, init_db, Player
from app.utils.cache import rate_limit, cached
import json
import time

player_bp = Blueprint('player', __name__)

@player_bp.route('/player/<chat_id>', methods=['GET'])
@rate_limit(max_requests=60, window=60)  # 60 запросов в минуту
def get_player(chat_id):
    """Get player data (с кэшем)"""
    conn = get_db()
    player = Player.get_by_chat_id(conn, chat_id)
    conn.close()
    return jsonify(player)

@player_bp.route('/click/<chat_id>', methods=['POST'])
@rate_limit(max_requests=120, window=60)  # 120 кликов в минуту (2 в секунду)
def click(chat_id):
    """Handle click action"""
    conn = get_db()
    result = Player.process_click(conn, chat_id)
    conn.close()
    return jsonify(result)
