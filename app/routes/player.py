from flask import Blueprint, jsonify, request
from app.database import get_player_data, process_click
from app.utils.cache import rate_limit

player_bp = Blueprint('player', __name__)

@player_bp.route('/player/<chat_id>', methods=['GET'])
@rate_limit(max_requests=60, window=60)
def get_player(chat_id):
    """Get player data"""
    player = get_player_data(chat_id)
    return jsonify(player)

@player_bp.route('/click/<chat_id>', methods=['POST'])
@rate_limit(max_requests=120, window=60)
def click(chat_id):
    """Handle click action"""
    result = process_click(chat_id)
    return jsonify(result)
