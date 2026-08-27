from flask import Blueprint, jsonify
from services.upgrades import buy_upgrade
from database import get_player

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/api/shop', methods=['GET'])
def get_shop():
    from config import config
    return jsonify(config.UPGRADES)

@shop_bp.route('/api/buy/<chat_id>/<upgrade_id>', methods=['POST'])
def buy_upgrade_api(chat_id, upgrade_id):
    player_row = get_player(chat_id)
    if not player_row:
        return jsonify({"error": "Player not found"}), 404
    
    player = dict(player_row)
    result, error = buy_upgrade(player, upgrade_id)
    
    if error:
        return jsonify({"error": error}), 400
    
    return jsonify(result)
