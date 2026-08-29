from flask import Blueprint, jsonify, request
from app.database import get_db, init_db
import json
import time

player_bp = Blueprint('player', __name__)

@player_bp.route('/player/<chat_id>', methods=['GET'])
def get_player(chat_id):
    """Get player data"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        ref_code = str(int(time.time()))[-6:]
        c.execute('''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, 
            upgrades, last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult, event_data)
            VALUES (?, 0, 0, 1, 0, 10, '{}', ?, '[]', 0, ?, '{}', 0, 1.0, '{}')''', 
            (chat_id, time.time(), ref_code))
        conn.commit()
        c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
        row = c.fetchone()
    
    player = dict(row) if row else {}
    player["upgrades"] = json.loads(player.get("upgrades") or "{}")
    player["achievements"] = json.loads(player.get("achievements") or "[]")
    player["event_data"] = json.loads(player.get("event_data") or "{}")
    
    conn.close()
    return jsonify(player)

@player_bp.route('/click/<chat_id>', methods=['POST'])
def click(chat_id):
    """Handle click action"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT click_power, balance, clicks, upgrades, total_earned, prestige_mult FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        ref_code = str(int(time.time()))[-6:]
        c.execute('''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, upgrades, 
            last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult, event_data)
            VALUES (?, 10, 1, 1, 0, 10, '{}', ?, '[]', 10, ?, '{}', 0, 1.0, '{}')''', 
            (chat_id, time.time(), ref_code))
        conn.commit()
        result = {"balance": 10, "clicks": 1, "level": 1, "click_power": 10, "upgrades": {}, "total_earned": 10, "prestige_mult": 1.0}
    else:
        rd = dict(row)
        pwr = rd.get("click_power") or 10
        mult = float(rd.get("prestige_mult") or 1.0)
        dmg = int(pwr * mult)
        
        nb = (rd.get("balance") or 0) + dmg
        nc = (rd.get("clicks") or 0) + 1
        nt = (rd.get("total_earned") or 0) + dmg
        
        c.execute('UPDATE players SET balance=?, clicks=?, total_earned=?, last_update=? WHERE chat_id=?', 
                 (nb, nc, nt, time.time(), chat_id))
        conn.commit()
        
        result = {
            "balance": nb, "clicks": nc, "level": (nc//100)+1, "click_power": pwr,
            "upgrades": json.loads(rd.get("upgrades") or "{}"),
            "total_earned": nt, "prestige_mult": mult
        }
    
    conn.close()
    return jsonify(result)
