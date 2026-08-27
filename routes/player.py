from flask import Blueprint, jsonify, request
from database import get_player, create_player, update_player
from services.quests import get_quests_data, save_quests_data
import time

player_bp = Blueprint('player', __name__)

@player_bp.route('/api/player/<chat_id>', methods=['GET'])
def get_player_api(chat_id):
    player_row = get_player(chat_id)
    
    if not player_row:
        # Создаем нового игрока
        ref_code = str(int(time.time()))[-6:]
        create_player(chat_id, ref_code)
        player_row = get_player(chat_id)
    
    # Преобразуем row в dict
    player = dict(player_row)
    player["upgrades"] = __import__('json').loads(player["upgrades"] or "{}")
    player["achievements"] = __import__('json').loads(player["achievements"] or "[]")
    player["quests_data"] = get_quests_data(player)
    player["prestige_points"] = player.get("prestige_points") or 0
    player["prestige_mult"] = float(player.get("prestige_mult") or 1.0)
    player["total_prestiges"] = player.get("total_prestiges") or 0
    
    # Пассивный доход
    now = time.time()
    mult = player["prestige_mult"]
    if player["last_update"] and player["passive_income"] > 0:
        sec = now - player["last_update"]
        if sec > 1:
            earned = int(player["passive_income"] * sec * mult)
            player["balance"] += earned
            player["total_earned"] += earned
            
            # Реферальный доход
            if player.get("referred_by"):
                bonus = int(earned * 0.01)
                if bonus > 0:
                    from database import get_connection
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute('UPDATE players SET balance = balance + ? WHERE chat_id = ?', (bonus, player["referred_by"]))
                    conn.commit()
                    conn.close()
            
            update_player(chat_id, balance=player["balance"], total_earned=player["total_earned"], last_update=now)
    
    player["last_update"] = now
    return jsonify(player)

@player_bp.route('/api/click/<chat_id>', methods=['POST'])
def click_api(chat_id):
    player_row = get_player(chat_id)
    
    if not player_row:
        ref_code = str(int(time.time()))[-6:]
        create_player(chat_id, ref_code)
        player_row = get_player(chat_id)
    
    player = dict(player_row)
    pwr = player.get("click_power") or 10
    mult = float(player.get("prestige_mult") or 1.0)
    final_pwr = int(pwr * mult)
    
    nb = (player.get("balance") or 0) + final_pwr
    nc = (player.get("clicks") or 0) + 1
    nt = (player.get("total_earned") or 0) + final_pwr
    
    update_player(chat_id, balance=nb, clicks=nc, total_earned=nt, last_update=time.time())
    
    return jsonify({
        "balance": nb,
        "clicks": nc,
        "level": (nc // 100) + 1,
        "click_power": pwr,
        "upgrades": __import__('json').loads(player.get("upgrades") or "{}"),
        "total_earned": nt,
        "prestige_mult": mult
    })
