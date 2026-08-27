from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import time
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        chat_id TEXT PRIMARY KEY, balance INTEGER DEFAULT 0, clicks INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1, passive_income INTEGER DEFAULT 0, click_power INTEGER DEFAULT 10,
        upgrades TEXT DEFAULT '{}', last_update REAL DEFAULT 0, achievements TEXT DEFAULT '[]',
        total_earned INTEGER DEFAULT 0, referral_code TEXT DEFAULT '', referred_by TEXT DEFAULT '',
        referral_earnings INTEGER DEFAULT 0, quests_data TEXT DEFAULT '{}'
    )''')
    
    # Безопасное добавление колонок (игнорирует ошибку если уже есть)
    for col, default in [("quests_data", "'{}'")]:
        try: c.execute(f"ALTER TABLE players ADD COLUMN {col} TEXT DEFAULT {default}")
        except: pass
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('players.db')
    conn.row_factory = sqlite3.Row
    return conn

UPGRADES = {
    "shawarma": {"name": "Ларёк", "cost": 100, "income": 2, "icon": "", "type": "passive"},
    "coffee": {"name": "Кофе", "cost": 500, "income": 10, "icon": "☕", "type": "passive"},
    "office": {"name": "Офис", "cost": 2000, "income": 50, "icon": "", "type": "passive"},
    "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "", "type": "passive"},
    "mouse": {"name": "Золотая мышь", "cost": 200, "power": 5, "icon": "🖱️", "type": "click"},
    "ai_bot": {"name": "AI-Бот", "cost": 1000, "power": 25, "icon": "", "type": "click"}
}

QUESTS = [
    {"id": "click_50", "name": "Трудяга", "desc": "Сделай 50 кликов", "target": 50, "type": "clicks", "reward": 150, "daily": True},
    {"id": "earn_500", "name": "Бизнесмен", "desc": "Заработай 500$", "target": 500, "type": "total_earned", "reward": 200, "daily": True},
    {"id": "first_buy", "name": "Инвестор", "desc": "Купи любое улучшение", "target": 1, "type": "upgrades_count", "reward": 300, "daily": False},
    {"id": "level_5", "name": "Менеджер", "desc": "Достигни 5 уровня", "target": 5, "type": "level", "reward": 500, "daily": False}
]

@app.route('/')
def index(): return send_from_directory('.', 'index.html')

def update_quests(player, conn):
    today = datetime.now().strftime("%Y-%m-%d")
    q_data = json.loads(player.get("quests_data", "{}"))
    c = conn.cursor()
    
    for q in QUESTS:
        qid = q["id"]
        if qid not in q_data:
            q_data[qid] = {"progress": 0, "claimed": False, "last_date": today}
        
        # Сброс дневных квестов
        if q["daily"] and q_data[qid]["last_date"] != today:
            q_data[qid] = {"progress": 0, "claimed": False, "last_date": today}
        
        # Расчет прогресса
        val = 0
        if q["type"] == "clicks": val = player.get("clicks", 0)
        elif q["type"] == "total_earned": val = player.get("total_earned", 0)
        elif q["type"] == "upgrades_count": val = sum(player.get("upgrades", {}).values())
        elif q["type"] == "level": val = player.get("level", 1)
        
        q_data[qid]["progress"] = min(val, q["target"])
        if q_data[qid]["progress"] >= q["target"] and not q_data[qid]["claimed"]:
            pass # Готов к получению
            
    c.execute("UPDATE players SET quests_data = ? WHERE chat_id = ?", (json.dumps(q_data), player["chat_id"]))
    conn.commit()
    return q_data

@app.route('/api/player/<chat_id>', methods=['GET'])
def get_player(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        ref_code = str(int(time.time()))[-6:]
        c.execute('''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, upgrades, last_update, achievements, total_earned, referral_code, quests_data)
            VALUES (?, 0, 0, 1, 0, 10, '{}', ?, '[]', 0, ?, '{}')''', (chat_id, time.time(), ref_code))
        conn.commit()
        player = {"chat_id": chat_id, "balance": 0, "clicks": 0, "level": 1, "passive_income": 0, "click_power": 10, "upgrades": {}, "last_update": time.time(), "achievements": [], "total_earned": 0, "referral_code": ref_code, "referred_by": "", "quests_data": {}}
    else:
        player = dict(row)
        player.update({"upgrades": json.loads(player["upgrades"]), "achievements": json.loads(player["achievements"]), "quests_data": json.loads(player["quests_data"])})
        
        now = time.time()
        if player["last_update"] and player["passive_income"] > 0:
            sec = now - player["last_update"]
            if sec > 1:
                earned = int(player["passive_income"] * sec)
                player["balance"] += earned
                player["total_earned"] += earned
                if player.get("referred_by"):
                    bonus = int(earned * 0.01)
                    if bonus > 0: c.execute('UPDATE players SET balance = balance + ? WHERE chat_id = ?', (bonus, player["referred_by"]))
                c.execute('UPDATE players SET balance = ?, total_earned = ?, last_update = ? WHERE chat_id = ?', (player["balance"], player["total_earned"], now, chat_id))
        player["last_update"] = now
        
    q_data = update_quests(player, conn)
    player["quests_data"] = q_data
    conn.close()
    return jsonify(player)

@app.route('/api/click/<chat_id>', methods=['POST'])
def click(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT click_power, balance, clicks, upgrades, total_earned FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    if not row:
        c.execute('''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, upgrades, last_update, achievements, total_earned, referral_code, quests_data) VALUES (?, 10, 1, 1, 0, 10, '{}', ?, '[]', 10, ?, '{}')''', (chat_id, time.time(), str(int(time.time()))[-6:]))
        conn.commit()
        res = {"balance": 10, "clicks": 1, "level": 1, "click_power": 10, "upgrades": {}, "total_earned": 10}
    else:
        pwr = row["click_power"] or 10
        nb = row["balance"] + pwr
        nc = row["clicks"] + 1
        nt = row["total_earned"] + pwr
        c.execute('UPDATE players SET balance=?, clicks=?, total_earned=?, last_update=? WHERE chat_id=?', (nb, nc, nt, time.time(), chat_id))
        conn.commit()
        res = {"balance": nb, "clicks": nc, "level": (nc//100)+1, "click_power": pwr, "upgrades": json.loads(row["upgrades"]), "total_earned": nt}
    conn.close()
    return jsonify(res)

@app.route('/api/shop', methods=['GET'])
def get_shop(): return jsonify(UPGRADES)

@app.route('/api/buy/<chat_id>/<upgrade_id>', methods=['POST'])
def buy_upgrade(chat_id, upgrade_id):
    if upgrade_id not in UPGRADES: return jsonify({"error": "Error"}), 400
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT balance, upgrades, click_power, passive_income FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    if not row: conn.close(); return jsonify({"error": "Not found"}), 404
    p = dict(row); p["upgrades"] = json.loads(p["upgrades"])
    u = UPGRADES[upgrade_id]
    cnt = p["upgrades"].get(upgrade_id, 0)
    price = int(u["cost"] * (1.15 ** cnt))
    if p["balance"] < price: conn.close(); return jsonify({"error": "Мало денег"}), 400
    
    nb = p["balance"] - price
    nu = {**p["upgrades"], upgrade_id: cnt+1}
    npwr = p["click_power"] or 10; npass = p["passive_income"] or 0
    if u["type"] == "click": npwr += u.get("power", 0)
    else: npass += u.get("income", 0)
    
    c.execute('UPDATE players SET balance=?, upgrades=?, click_power=?, passive_income=?, last_update=? WHERE chat_id=?', (nb, json.dumps(nu), npwr, npass, time.time(), chat_id))
    conn.commit(); conn.close()
    return jsonify({"balance": nb, "click_power": npwr, "passive_income": npass, "upgrades": nu, "success": True})

@app.route('/api/quests/<chat_id>', methods=['GET'])
def get_quests(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT quests_data, chat_id FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    if not row: return jsonify([])
    q_data = json.loads(row["quests_data"])
    res = []
    for q in QUESTS:
        status = q_data.get(q["id"], {"progress":0, "claimed":False})
        res.append({**q, "progress": status["progress"], "claimed": status["claimed"], "chat_id": row["chat_id"]})
    return jsonify(res)

@app.route('/api/claim_quest/<chat_id>/<quest_id>', methods=['POST'])
def claim_quest(chat_id, quest_id):
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT quests_data, balance FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    if not row: conn.close(); return jsonify({"error": "Not found"}), 404
    
    q_data = json.loads(row["quests_data"])
    if quest_id not in q_data or q_data[quest_id]["claimed"]:
        conn.close(); return jsonify({"error": "Already claimed"}), 400
        
    quest_def = next((q for q in QUESTS if q["id"] == quest_id), None)
    if not quest_def or q_data[quest_id]["progress"] < quest_def["target"]:
        conn.close(); return jsonify({"error": "Not ready"}), 400
        
    q_data[quest_id]["claimed"] = True
    nb = row["balance"] + quest_def["reward"]
    c.execute('UPDATE players SET balance=?, quests_data=? WHERE chat_id=?', (nb, json.dumps(q_data), chat_id))
    conn.commit(); conn.close()
    return jsonify({"success": True, "balance": nb, "reward": quest_def["reward"]})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT chat_id, balance, level FROM players ORDER BY balance DESC LIMIT 50')
    conn.close()
    return jsonify([{"rank":i+1, "chat_id":r["chat_id"], "balance":r["balance"], "level":r["level"]} for i,r in enumerate(c.fetchall())])

@app.route('/api/referral_link/<chat_id>', methods=['GET'])
def get_referral_link(chat_id):
    conn = get_db(); c = conn.cursor(); c.execute('SELECT referral_code FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone(); conn.close()
    if not row: return jsonify({"error": "Not found"}), 404
    bot = request.args.get('bot', 'MagnatZeroBot')
    return jsonify({"link": f"https://t.me/{bot}?start=ref_{row['referral_code']}", "code": row["referral_code"]})

@app.route('/api/bind_referral/<chat_id>/<ref_code>', methods=['POST'])
def bind_referral(chat_id, ref_code):
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT referred_by FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    if not row or row["referred_by"]: conn.close(); return jsonify({"error": "Already bound"}), 400
    c.execute('SELECT chat_id FROM players WHERE referral_code = ?', (ref_code,))
    ref = c.fetchone()
    if not ref or ref["chat_id"] == chat_id: conn.close(); return jsonify({"error": "Invalid"}), 400
    c.execute('UPDATE players SET referred_by = ? WHERE chat_id = ?', (ref["chat_id"], chat_id))
    c.execute('UPDATE players SET balance = balance + 500 WHERE chat_id IN (?, ?)', (ref["chat_id"], chat_id))
    conn.commit(); conn.close()
    return jsonify({"success": True, "bonus": 500})

init_db()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
