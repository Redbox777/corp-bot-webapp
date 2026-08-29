"""
Game Service - Игровая логика
"""
from flask import Blueprint, jsonify, request
import time
import json

game_bp = Blueprint('game', __name__, url_prefix='/api/game')

# Game state
game_state = {
    "players": {},
    "boss": {
        "name": "Огненный Дракон",
        "hp": 10000,
        "max_hp": 10000,
        "level": 1
    }
}

@game_bp.route('/player/<chat_id>', methods=['GET'])
def get_player(chat_id):
    """Получить игрока"""
    if chat_id not in game_state["players"]:
        game_state["players"][chat_id] = {
            "chat_id": chat_id,
            "balance": 0,
            "clicks": 0,
            "level": 1,
            "click_power": 10,
            "created_at": time.time()
        }
    
    return jsonify(game_state["players"][chat_id])

@game_bp.route('/click/<chat_id>', methods=['POST'])
def click(chat_id):
    """Обработать клик"""
    if chat_id not in game_state["players"]:
        game_state["players"][chat_id] = {
            "chat_id": chat_id,
            "balance": 0,
            "clicks": 0,
            "level": 1,
            "click_power": 10
        }
    
    player = game_state["players"][chat_id]
    player["clicks"] += 1
    player["balance"] += player["click_power"]
    
    # Level up every 100 clicks
    player["level"] = player["clicks"] // 100 + 1
    
    # Damage to boss
    boss_damage = player["click_power"] // 2
    game_state["boss"]["hp"] -= boss_damage
    
    # Boss respawn
    if game_state["boss"]["hp"] <= 0:
        reward = game_state["boss"]["max_hp"] * 2
        player["balance"] += reward
        game_state["boss"]["level"] += 1
        game_state["boss"]["hp"] = game_state["boss"]["max_hp"] * 1.5
        game_state["boss"]["max_hp"] *= 1.5
        
        return jsonify({
            "player": player,
            "boss_killed": True,
            "reward": reward,
            "new_boss_level": game_state["boss"]["level"]
        })
    
    return jsonify({
        "player": player,
        "boss": game_state["boss"],
        "boss_damage": boss_damage
    })

@game_bp.route('/boss', methods=['GET'])
def get_boss():
    """Получить статус босса"""
    return jsonify(game_state["boss"])

@game_bp.route('/stats', methods=['GET'])
def get_stats():
    """Статистика игрового сервиса"""
    return jsonify({
        "total_players": len(game_state["players"]),
        "boss_level": game_state["boss"]["level"],
        "boss_hp": game_state["boss"]["hp"]
    })
