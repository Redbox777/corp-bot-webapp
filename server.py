from flask import Flask, jsonify, request, send_from_directory
import os
import time
import sqlite3
import json

app = Flask(__name__)

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
            last_update REAL DEFAULT 0
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
    "shawarma": {"name": "Ларёк с шаурмой", "cost": 100, "income": 2, "icon": "🌯"},
    "coffee": {"name": "Кофейная точка", "cost": 500, "income": 10, "icon": "☕"},
    "office": {"name": "Офис", "cost": 2000, "income": 50, "icon": "🏢"},
    "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "🏭"},
    "crypto": {"name": "Крипто-ферма", "cost": 50000, "income": 1000, "icon": "₿"}
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
        # Создаём нового игрока
        c.execute('''
            INSERT INTO players (chat_id, balance, clicks, level, passive_income, upgrades, last_update)
            VALUES (?, 0, 0, 1, 0, '{}', ?)
        ''', (chat_id, time.time()))
        conn.commit()
        player = {
            "balance": 0, "clicks": 0, "level": 1, 
            "passive_income": 0, "upgrades": {}, "last_update": time.time()
        }
    else:
        player = dict(row)
        player["upgrades"] = json.loads(player["upgrades"])
        
        # Начисляем пассивный доход за время оффлайн
        now = time.time()
        if player["last_update"] and player["passive_income"] > 0:
            seconds = now - player["last_update"]
            if seconds > 1:
                earned = int(player["passive_income"] * seconds)
                player["balance"] += earned
                c.execute('''
                    UPDATE players SET balance = ?, last_update = ? WHERE chat_id = ?
                ''', (player["balance"], now, chat_id))
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
            INSERT INTO players (chat_id, balance, clicks, level, passive_income, upgrades, last_update)
            VALUES (?, 10, 1, 1, 0, '{}', ?)
        ''', (chat_id, time.time()))
    else:
        c.execute('''
            UPDATE players 
            SET balance = balance + 10, clicks = clicks + 1, 
                level = (clicks + 1) / 100 + 1, last_update = ?
            WHERE chat_id = ?
        ''', (time.time(), chat_id))
    
    conn.commit()
    
    # Получаем обновлённые данные
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
    
    # Динамическая цена
    current_count = player["upgrades"].get(upgrade_id, 0)
    current_price = int(upgrade["cost"] * (1.15 ** current_count))
    
    if player["balance"] < current_price:
        conn.close()
        return jsonify({"error": "Недостаточно монет"}), 400
    
    # Покупаем
    new_count = current_count + 1
    new_passive = player["passive_income"] + upgrade["income"]
    
    c.execute('''
        UPDATE players 
        SET balance = balance - ?, 
            upgrades = ?, 
            passive_income = ?,
            last_update = ?
        WHERE chat_id = ?
    ''', (current_price, json.dumps({**player["upgrades"], upgrade_id: new_count}), 
          new_passive, time.time(), chat_id))
    
    conn.commit()
    
    # Получаем обновлённые данные
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    
    player = dict(row)
    player["upgrades"] = json.loads(player["upgrades"])
    
    next_price = int(upgrade["cost"] * (1.15 ** new_count))
    
    return jsonify({
        "balance": player["balance"],
        "passive_income": player["passive_income"],
        "upgrades": player["upgrades"],
        "next_price": next_price,
        "success": True
    })

# Инициализируем БД при запуске
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
