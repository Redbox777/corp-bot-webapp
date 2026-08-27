from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import time
import sqlite3
import json
from datetime import datetime, timedelta

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
            last_daily TEXT DEFAULT '',
            achievements TEXT DEFAULT '[]',
            total_earned INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('players.db')
    conn.row_factory = sqlite3.Row
    return conn

# Магазин улучшений
UPGRADES = {
    "shawarma": {"name": "Ларёк", "cost": 100, "income": 2, "icon": ""},
    "coffee": {"name": "Кофе", "cost": 500, "income": 10, "icon": "☕"},
    "office": {"name": "Офис", "cost": 2000, "income": 50, "icon": ""},
    "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "🏭"},
    "crypto": {"name": "Крипта", "cost": 50000, "income": 1000, "icon": "₿"},
    "bank": {"name": "Банк", "cost": 200000, "income": 5000, "icon": "🏦"}
}

# Система достижений
ACHIEVEMENTS = [
    {"id": "first_click", "name": "Первый шаг", "desc": "Сделайте первый клик", "reward": 50, "icon": "👆"},
    {"id": "hundred_clicks", "name": "Трудяга", "desc": "100 кликов", "reward": 200, "icon": "💪"},
    {"id": "thousand_clicks", "name": "Магнат", "desc": "1000 кликов", "reward": 1000, "icon": "🏆"},
    {"id": "first_business", "name": "Предприниматель", "desc": "Купите первый бизнес", "reward": 100, "icon": "💼"},
    {"id": "rich", "name": "Богач", "desc": "Накопите 10000$", "reward": 500, "icon": "💰"},
    {"id": "tycoon", "name": "Магнат", "desc": "Накопите 100000$", "reward": 2500, "icon": "👑"},
    {"id": "daily_week", "name": "Постоянный", "desc": "7 дней подряд", "reward": 1000, "icon": "📅"}
]

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
        c.execute('''
            INSERT INTO players (chat_id, balance, clicks, level, passive_income, upgrades, last_update, last_daily, achievements, total_earned)
            VALUES (?, 0, 0, 1, 0, '{}', ?, '', '[]', 0)
        ''', (chat_id, time.time()))
        conn.commit()
        player = {
            "balance": 0, "clicks": 0, "level": 1, "passive_income": 0, 
            "upgrades": {}, "last_update": time.time(), "last_daily": "", 
            "achievements": [], "total_earned": 0
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
                c.execute('UPDATE players SET balance = ?, total_earned = ?, last_update = ? WHERE chat_id = ?',
                         (player["balance"], player["total_earned"], now, chat_id))
                conn.commit()
        else:
            player["last_update"] = now
    
    # Проверка достижений
    new_achievements = check_achievements(player)
    if new_achievements:
        player["achievements"].extend(new_achievements)
        c.execute('UPDATE players SET achievements = ? WHERE chat_id = ?',
                 (json.dumps(player["achievements"]), chat_id))
        conn.commit()
    
    conn.close()
    return jsonify(player)

def check_achievements(player):
    new = []
    achieved = player.get("achievements", [])
    
    if player.get("clicks", 0) >= 1 and "first_click" not in achieved:
        new.append({"id": "first_click", "reward": 50})
        player["balance"] = player.get("balance", 0) + 50
    if player.get("clicks", 0) >= 100 and "hundred_clicks" not in achieved:
        new.append({"id": "hundred_clicks", "reward": 200})
        player["balance"] += 200
    if player.get("clicks", 0) >= 1000 and "thousand_clicks" not in achieved:
        new.append({"id": "thousand_clicks", "reward": 1000})
        player["balance"] += 1000
    if len(player.get("upgrades", {})) >= 1 and "first_business" not in achieved:
        new.append({"id": "first_business", "reward": 100})
        player["balance"] += 100
    if player.get("balance", 0) >= 10000 and "rich" not in achieved:
        new.append({"id": "rich", "reward": 500})
        player["balance"] += 500
    if player.get("balance", 0) >= 100000 and "tycoon" not in achieved:
        new.append({"id": "tycoon", "reward": 2500})
        player["balance"] += 2500
    
    return new

@app.route('/api/daily', methods=['POST'])
def daily_bonus(chat_id=None):
    if not chat_id:
        return jsonify({"error": "No chat_id"}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    
    player = dict(row)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if player["last_daily"] == today:
        conn.close()
        return jsonify({"already_claimed": True, "message": "Приходите завтра!"})
    
    # Считаем дни подряд
    last_date = datetime.strptime(player["last_daily"], "%Y-%m-%d") if player["last_daily"] else None
    streak = 1
    if last_date:
        diff = (datetime.now() - last_date).days
        if diff == 1:
            streak = min(player.get("daily_streak", 0) + 1, 7)
        elif diff > 1:
            streak = 1
    
    bonus = 100 * streak
    c.execute('''
        UPDATE players SET balance = balance + ?, last_daily = ?, daily_streak = ? WHERE chat_id = ?
    ''', (bonus, today, streak, chat_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "bonus": bonus, "streak": streak})

@app.route('/api/click/<chat_id>', methods=['POST'])
def click(chat_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        c.execute('''
            INSERT INTO players (chat_id, balance, clicks, level, passive_income, upgrades, last_update, last_daily, achievements, total_earned)
            VALUES (?, 10, 1, 1, 0, '{}', ?, '', '[]', 10)
        ''', (chat_id, time.time()))
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
    player["achievements"] = json.loads(player["achievements"])
    return jsonify(player)

@app.route('/api/shop', methods=['GET'])
def get_shop():
    return jsonify(UPGRADES)

@app.route('/api/buy/<chat_id>/<upgrade_id>', methods=['POST'])
def buy_upgrade(chat_id, upgrade_id):
    if upgrade_id not in UPGRADES:
        return jsonify({"error": "Invalid upgrade"}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"error": "Player not found"}), 404
    
    player = dict(row)
    player["upgrades"] = json.loads(player["upgrades"])
    upgrade = UPGRADES[upgrade_id]
    
    current_count = player["upgrades"].get(upgrade_id, 0)
    current_price = int(upgrade["cost"] * (1.15 ** current_count))
    
    if player["balance"] < current_price:
        conn.close()
        return jsonify({"error": "Недостаточно монет"}), 400
    
    new_count = current_count + 1
    new_passive = player["passive_income"] + upgrade["income"]
    
    c.execute('''
        UPDATE players 
        SET balance = balance - ?, upgrades = ?, passive_income = ?, last_update = ?
        WHERE chat_id = ?
    ''', (current_price, json.dumps({**player["upgrades"], upgrade_id: new_count}), 
          new_passive, time.time(), chat_id))
    
    conn.commit()
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    
    player = dict(row)
    player["upgrades"] = json.loads(player["upgrades"])
    next_price = int(upgrade["cost"] * (1.15 ** new_count))
    
    return jsonify({
        "balance": player["balance"], "passive_income": player["passive_income"],
        "upgrades": player["upgrades"], "next_price": next_price, "success": True
    })

@app.route('/api/achievements', methods=['GET'])
def get_achievements():
    return jsonify(ACHIEVEMENTS)

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
