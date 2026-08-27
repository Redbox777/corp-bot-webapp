from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import time
import sqlite3
import json

app = Flask(__name__)
CORS(app)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS players (
                chat_id TEXT PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                passive_income INTEGER DEFAULT 0,
                click_power INTEGER DEFAULT 10,
                upgrades TEXT DEFAULT '{}',
                last_update REAL DEFAULT 0,
                achievements TEXT DEFAULT '[]',
                total_earned INTEGER DEFAULT 0,
                referral_code TEXT DEFAULT '',
                referred_by TEXT DEFAULT '',
                referral_earnings INTEGER DEFAULT 0
            )
        ''')
    except sqlite3.OperationalError:
        # Если таблица уже есть, пробуем добавить новую колонку (если её нет)
        try:
            c.execute('ALTER TABLE players ADD COLUMN click_power INTEGER DEFAULT 10')
        except sqlite3.OperationalError:
            pass # Колонка уже есть
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('players.db')
    conn.row_factory = sqlite3.Row
    return conn

# Магазин (Бизнес + Клик)
UPGRADES = {
    # Бизнесы (Пассивный доход)
    "shawarma": {"name": "Ларёк", "cost": 100, "income": 2, "icon": "", "type": "passive"},
    "coffee": {"name": "Кофе", "cost": 500, "income": 10, "icon": "☕", "type": "passive"},
    "office": {"name": "Офис", "cost": 2000, "income": 50, "icon": "", "type": "passive"},
    "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "", "type": "passive"},
    
    # Улучшения клика (Активный доход)
    "mouse": {"name": "Золотая мышь", "cost": 200, "power": 5, "icon": "🖱️", "type": "click"},
    "ai_bot": {"name": "AI-Бот", "cost": 1000, "power": 25, "icon": "🤖", "type": "click"},
    "nano_tech": {"name": "Нанотех", "cost": 5000, "power": 100, "icon": "⚛️", "type": "click"}
}

REFERRAL_BONUS = 500

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/player/<chat_id>', methods=['GET'])
def get_player(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        ref_code = str(int(time.time()))[-6:]
        c.execute('''
            INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, upgrades, last_update, achievements, total_earned, referral_code)
            VALUES (?, 0, 0, 1, 0, 10, '{}', ?, '[]', 0, ?)
        ''', (chat_id, time.time(), ref_code))
        conn.commit()
        player = {
            "balance": 0, "clicks": 0, "level": 1, "passive_income": 0, "click_power": 10,
            "upgrades": {}, "last_update": time.time(), "achievements": [], "total_earned": 0,
            "referral_code": ref_code, "referred_by": ""
        }
    else:
        player = dict(row)
        player["upgrades"] = json.loads(player["upgrades"])
        player["achievements"] = json.loads(player["achievements"])
        
        # Пассивный доход
        now = time.time()
        if player["last_update"] and player["passive_income"] > 0:
            seconds = now - player["last_update"]
            if seconds > 1:
                earned = int(player["passive_income"] * seconds)
                player["balance"] += earned
                player["total_earned"] += earned
                
                # Реферальный доход
                if player.get("referred_by"):
                    bonus = int(earned * 0.01)
                    if bonus > 0:
                        c.execute('UPDATE players SET balance = balance + ? WHERE chat_id = ?', (bonus, player["referred_by"]))
                
                c.execute('UPDATE players SET balance = ?, total_earned = ?, last_update = ? WHERE chat_id = ?',
                         (player["balance"], player["total_earned"], now, chat_id))
                conn.commit()
        else:
            player["last_update"] = now
    
    conn.close()
    return jsonify(player)

@app.route('/api/click/<chat_id>', methods=['POST'])
def click(chat_id):
    conn = get_db()
    c = conn.cursor()
    
    # Получаем текущую силу клика
    c.execute('SELECT click_power, balance, clicks, upgrades, total_earned FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        # Создаем, если нет
        c.execute('''
            INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, upgrades, last_update, achievements, total_earned, referral_code)
            VALUES (?, 10, 1, 1, 0, 10, '{}', ?, '[]', 10, ?)
        ''', (chat_id, time.time(), str(int(time.time()))[-6:]))
        conn.commit()
        player = {"balance": 10, "clicks": 1, "level": 1, "click_power": 10, "upgrades": {}, "total_earned": 10}
    else:
        current_power = row["click_power"] or 10
        new_balance = row["balance"] + current_power
        new_clicks = row["clicks"] + 1
        new_total = row["total_earned"] + current_power
        
        c.execute('''
            UPDATE players SET balance = ?, clicks = ?, total_earned = ?, last_update = ? WHERE chat_id = ?
        ''', (new_balance, new_clicks, new_total, time.time(), chat_id))
        conn.commit()
        player = {"balance": new_balance, "clicks": new_clicks, "level": (new_clicks//100)+1, "click_power": current_power, "upgrades": json.loads(row["upgrades"]), "total_earned": new_total}
    
    conn.close()
    return jsonify(player)

@app.route('/api/shop', methods=['GET'])
def get_shop():
    return jsonify(UPGRADES)

@app.route('/api/buy/<chat_id>/<upgrade_id>', methods=['POST'])
def buy_upgrade(chat_id, upgrade_id):
    if upgrade_id not in UPGRADES: return jsonify({"error": "Error"}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT balance, upgrades, click_power, passive_income FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    
    player = dict(row)
    player["upgrades"] = json.loads(player["upgrades"])
    upgrade = UPGRADES[upgrade_id]
    
    count = player["upgrades"].get(upgrade_id, 0)
    price = int(upgrade["cost"] * (1.15 ** count))
    
    if player["balance"] < price:
        conn.close()
        return jsonify({"error": "Мало денег"}), 400
    
    new_balance = player["balance"] - price
    new_upgrades = {**player["upgrades"], upgrade_id: count + 1}
    
    new_power = player["click_power"] or 10
    new_passive = player["passive_income"] or 0
    
    # Применяем улучшение
    if upgrade["type"] == "click":
        new_power += upgrade.get("power", 0)
    else:
        new_passive += upgrade.get("income", 0)
    
    c.execute('''
        UPDATE players SET balance = ?, upgrades = ?, click_power = ?, passive_income = ?, last_update = ?
        WHERE chat_id = ?
    ''', (new_balance, json.dumps(new_upgrades), new_power, new_passive, time.time(), chat_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        "balance": new_balance, 
        "click_power": new_power, 
        "passive_income": new_passive, 
        "upgrades": new_upgrades, 
        "success": True
    })

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT chat_id, balance, level FROM players ORDER BY balance DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    return jsonify([{"rank": i+1, "chat_id": r["chat_id"], "balance": r["balance"], "level": r["level"]} for i, r in enumerate(rows)])

@app.route('/api/referral_link/<chat_id>', methods=['GET'])
def get_referral_link(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT referral_code FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    if not row: return jsonify({"error": "Not found"}), 404
    bot = request.args.get('bot', 'MagnatZeroBot')
    return jsonify({"link": f"https://t.me/{bot}?start=ref_{row['referral_code']}", "code": row["referral_code"]})

@app.route('/api/bind_referral/<chat_id>/<ref_code>', methods=['POST'])
def bind_referral(chat_id, ref_code):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT referred_by FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    if not row or row["referred_by"]:
        conn.close()
        return jsonify({"error": "Already bound"}), 400
    
    c.execute('SELECT chat_id FROM players WHERE referral_code = ?', (ref_code,))
    referrer = c.fetchone()
    if not referrer or referrer["chat_id"] == chat_id:
        conn.close()
        return jsonify({"error": "Invalid"}), 400
    
    ref_id = referrer["chat_id"]
    c.execute('UPDATE players SET referred_by = ? WHERE chat_id = ?', (ref_id, chat_id))
    c.execute('UPDATE players SET balance = balance + ? WHERE chat_id = ? OR chat_id = ?', (REFERRAL_BONUS, ref_id, chat_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "bonus": REFERRAL_BONUS})

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
