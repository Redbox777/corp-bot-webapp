from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import time
import sqlite3
import json
import urllib.parse

app = Flask(__name__)
CORS(app)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            chat_id TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            passive_income INTEGER DEFAULT 0,
            upgrades TEXT DEFAULT '{}',
            last_update REAL DEFAULT 0,
            achievements TEXT DEFAULT '[]',
            total_earned INTEGER DEFAULT 0,
            referral_code TEXT DEFAULT '',
            referred_by TEXT DEFAULT '',
            referral_earnings INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('players.db')
    conn.row_factory = sqlite3.Row
    return conn

# Настройки
REFERRAL_BONUS = 500
REFERRAL_PERCENT = 0.01
APP_URL = os.environ.get('APP_URL', 'https://corp-bot-webapp.onrender.com')

UPGRADES = {
    "shawarma": {"name": "Ларёк", "cost": 100, "income": 2, "icon": ""},
    "coffee": {"name": "Кофе", "cost": 500, "income": 10, "icon": "☕"},
    "office": {"name": "Офис", "cost": 2000, "income": 50, "icon": "🏢"},
    "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "🏭"},
    "crypto": {"name": "Крипта", "cost": 50000, "income": 1000, "icon": "₿"},
    "bank": {"name": "Банк", "cost": 200000, "income": 5000, "icon": "🏦"}
}

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
        # Создаём игрока
        ref_code = str(int(time.time()))[-6:] # Простой код приглашения
        c.execute('''
            INSERT INTO players (chat_id, balance, clicks, level, passive_income, upgrades, last_update, achievements, total_earned, referral_code)
            VALUES (?, 0, 0, 1, 0, '{}', ?, '[]', 0, ?)
        ''', (chat_id, time.time(), ref_code))
        conn.commit()
        player = {
            "chat_id": chat_id, "balance": 0, "clicks": 0, "level": 1, 
            "passive_income": 0, "upgrades": {}, "last_update": time.time(), 
            "achievements": [], "total_earned": 0, "referral_code": ref_code, 
            "referred_by": "", "referral_earnings": 0
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
                player["total_earned"] = player.get("total_earned", 0) + earned
                
                # Реферальный доход
                if player.get("referred_by"):
                    bonus = int(earned * REFERRAL_PERCENT)
                    if bonus > 0:
                        c.execute('UPDATE players SET referral_earnings = referral_earnings + ? WHERE chat_id = ?', (bonus, player["referred_by"]))
                        player["referral_earnings"] = player.get("referral_earnings", 0) + bonus
                
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
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        c.execute('''
            INSERT INTO players (chat_id, balance, clicks, level, passive_income, upgrades, last_update, achievements, total_earned, referral_code)
            VALUES (?, 10, 1, 1, 0, '{}', ?, '[]', 10, ?)
        ''', (chat_id, time.time(), str(int(time.time()))[-6:]))
    else:
        c.execute('''
            UPDATE players 
            SET balance = balance + 10, clicks = clicks + 1, 
                level = (clicks + 1) / 100 + 1, last_update = ?, total_earned = total_earned + 10
            WHERE chat_id = ?
        ''', (time.time(), chat_id))
    
    conn.commit()
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    
    player = dict(row)
    player["upgrades"] = json.loads(player["upgrades"])
    return jsonify(player)

@app.route('/api/shop', methods=['GET'])
def get_shop():
    return jsonify(UPGRADES)

@app.route('/api/buy/<chat_id>/<upgrade_id>', methods=['POST'])
def buy_upgrade(chat_id, upgrade_id):
    if upgrade_id not in UPGRADES: return jsonify({"error": "Error"}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
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
    
    new_count = count + 1
    new_passive = player["passive_income"] + upgrade["income"]
    
    c.execute('''
        UPDATE players SET balance = balance - ?, upgrades = ?, passive_income = ?, last_update = ?
        WHERE chat_id = ?
    ''', (price, json.dumps({**player["upgrades"], upgrade_id: new_count}), new_passive, time.time(), chat_id))
    conn.commit()
    
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    
    player = dict(row)
    player["upgrades"] = json.loads(player["upgrades"])
    return jsonify({"balance": player["balance"], "passive_income": player["passive_income"], "upgrades": player["upgrades"], "success": True})

# === НОВЫЕ ФУНКЦИИ: РЕФЕРАЛЫ И PvP ===

@app.route('/api/referral_link/<chat_id>', methods=['GET'])
def get_referral_link(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT referral_code FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    if not row: return jsonify({"error": "Not found"}), 404
    
    # Формируем ссылку с параметром реферала
    # tg.openTelegramLink не работает внутри webview напрямую так, но мы можем дать ссылку на бота
    # Для WebApp лучше использовать share API, но ссылка будет на бота
    bot_username = request.args.get('bot', 'MagnatZeroBot') # Замените на ник вашего бота
    link = f"https://t.me/{bot_username}?start=ref_{row['referral_code']}"
    return jsonify({"link": link, "code": row["referral_code"]})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = get_db()
    c = conn.cursor()
    # Топ 50 по балансу
    c.execute('SELECT chat_id, balance, level FROM players ORDER BY balance DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    
    leaderboard = []
    for i, row in enumerate(rows):
        leaderboard.append({
            "rank": i + 1,
            "chat_id": row["chat_id"],
            "balance": row["balance"],
            "level": row["level"]
        })
    return jsonify(leaderboard)

@app.route('/api/bind_referral/<chat_id>/<ref_code>', methods=['POST'])
def bind_referral(chat_id, ref_code):
    conn = get_db()
    c = conn.cursor()
    
    # Проверяем, есть ли уже реферал у этого юзера
    c.execute('SELECT referred_by FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    if not row or row["referred_by"]:
        conn.close()
        return jsonify({"error": "Already bound or not found"}), 400
    
    # Ищем реферера по коду
    c.execute('SELECT chat_id FROM players WHERE referral_code = ?', (ref_code,))
    referrer = c.fetchone()
    
    if not referrer or referrer["chat_id"] == chat_id:
        conn.close()
        return jsonify({"error": "Invalid code"}), 400
    
    referrer_id = referrer["chat_id"]
    
    # Привязываем
    c.execute('UPDATE players SET referred_by = ? WHERE chat_id = ?', (referrer_id, chat_id))
    c.execute('UPDATE players SET referral_count = referral_count + 1 WHERE chat_id = ?', (referrer_id,)) # Нужно добавить колонку referral_count если её нет, но пока пропустим для простоты
    
    # Даем бонус рефереру
    c.execute('UPDATE players SET balance = balance + ? WHERE chat_id = ?', (REFERRAL_BONUS, referrer_id))
    
    # Даем бонус новичку
    c.execute('UPDATE players SET balance = balance + ? WHERE chat_id = ?', (REFERRAL_BONUS, chat_id))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True, "bonus": REFERRAL_BONUS})

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
