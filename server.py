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
        referral_earnings INTEGER DEFAULT 0, quests_data TEXT DEFAULT '{}',
        prestige_points INTEGER DEFAULT 0, prestige_mult REAL DEFAULT 1.0, total_prestiges INTEGER DEFAULT 0
    )''')
    
    # Безопасное добавление колонок только если их нет
    cols = [
        ("prestige_points", "0"),
        ("prestige_mult", "1.0"),
        ("total_prestiges", "0")
    ]
    for col, default in cols:
        try:
            c.execute(f"PRAGMA table_info(players)")
            existing = [r[1] for r in c.fetchall()]
            if col not in existing:
                c.execute(f"ALTER TABLE players ADD COLUMN {col} REAL DEFAULT {default}")
        except:
            pass
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('players.db')
    conn.row_factory = sqlite3.Row
    return conn

UPGRADES = {
    "shawarma": {"name": "Ларёк", "cost": 100, "income": 2, "icon": "🌯", "type": "passive"},
    "coffee": {"name": "Кофе", "cost": 500, "income": 10, "icon": "", "type": "passive"},
    "office": {"name": "Офис", "cost": 2000, "income": 50, "icon": "🏢", "type": "passive"},
    "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "🏭", "type": "passive"},
    "bank": {"name": "Банк", "cost": 50000, "income": 1500, "icon": "🏦", "type": "passive"},
    "mouse": {"name": "Золотая мышь", "cost": 200, "power": 5, "icon": "️", "type": "click"},
    "ai_bot": {"name": "AI-Бот", "cost": 1000, "power": 25, "icon": "🤖", "type": "click"},
    "quantum": {"name": "Квантовый ПК", "cost": 100000, "power": 500, "icon": "💻", "type": "click"}
}

QUESTS = [
    {"id": "click_100", "name": "Кликер", "desc": "Сделай 100 кликов", "target": 100, "type": "clicks", "reward": 200, "daily": True},
    {"id": "earn_1000", "name": "Магнат", "desc": "Заработай 1000$", "target": 1000, "type": "total_earned", "reward": 500, "daily": True},
    {"id": "rebirth_1", "name": "Новая жизнь", "desc": "Переродись 1 раз", "target": 1, "type": "prestiges", "reward": 1000, "daily": False}
]

@app.route('/')
def index(): return send_from_directory('.', 'index.html')

@app.route('/health')
def health(): return jsonify({"status": "ok"})

def update_quests(player, conn):
    today = datetime.now().strftime("%Y-%m-%d")
    q_data = json.loads(player.get("quests_data") or "{}")
    c = conn.cursor()
    for q in QUESTS:
        qid = q["id"]
        if qid not in q_data: q_data[qid] = {"progress": 0, "claimed": False, "last_date": today}
        if q["daily"] and q_data[qid]["last_date"] != today:
            q_data[qid] = {"progress": 0, "claimed": False, "last_date": today}
        val = 0
        t = q["type"]
        if t == "clicks": val = player.get("clicks", 0)
        elif t == "total_earned": val = player.get("total_earned", 0)
        elif t == "upgrades_count": val = sum((player.get("upgrades") or {}).values())
        elif t == "level": val = player.get("level", 1)
        elif t == "prestiges": val = player.get("total_prestiges", 0)
        q_data[qid]["progress"] = min(val, q["target"])
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
        c.execute('''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, upgrades, last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult)
            VALUES (?, 0, 0, 1, 0, 10, '{}', ?, '[]', 0, ?, '{}', 0, 1.0)''', (chat_id, time.time(), ref_code))
        conn.commit()
        player = {"chat_id": chat_id, "balance": 0, "clicks": 0, "level": 1, "passive_income": 0, "click_power": 10, "upgrades": {}, "last_update": time.time(), "achievements": [], "total_earned": 0, "referral_code": ref_code, "referred_by": "", "prestige_points": 0, "prestige_mult": 1.0, "total_prestiges": 0, "quests_data": {}}
    else:
        player = dict(row)
        # Безопасная загрузка JSON с fallback
        player["upgrades"] = json.loads(player["upgrades"] or "{}")
        player["achievements"] = json.loads(player["achievements"] or "[]")
        player["quests_data"] = json.loads(player["quests_data"] or "{}")
        player["prestige_points"] = player.get("prestige_points") or 0
        player["prestige_mult"] = float(player.get("prestige_mult") or 1.0)
        player["total_prestiges"] = player.get("total_prestiges") or 0
        
        now = time.time()
        mult = player["prestige_mult"]
        if player["last_update"] and player["passive_income"] > 0:
            sec = now - player["last_update"]
            if sec > 1:
                earned = int(player["passive_income"] * sec * mult)
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
    c.execute('SELECT click_power, balance, clicks, upgrades, total_earned, prestige_mult FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    if not row:
        c.execute('''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, upgrades, last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult) VALUES (?, 10, 1, 1, 0, 10, '{}', ?, '[]', 10, ?, '{}', 0, 1.0)''', (chat_id, time.time(), str(int(time.time()))[-6:]))
        conn.commit()
        res = {"balance": 10, "clicks": 1, "level": 1, "click_power": 10, "upgrades": {}, "total_earned": 10, "prestige_mult": 1.0}
    else:
        pwr = row["click_power"] or 10
        mult = float(row.get("prestige_mult") or 1.0)
        final_pwr = int(pwr * mult)
        nb = (row["balance"] or 0) + final_pwr
        nc = (row["clicks"] or 0) + 1
        nt = (row["total_earned"] or 0) + final_pwr
        c.execute('UPDATE players SET balance=?, clicks=?, total_earned=?, last_update=? WHERE chat_id=?', (nb, nc, nt, time.time(), chat_id))
        conn.commit()
        res = {"balance": nb, "clicks": nc, "level": (nc//100)+1, "click_power": pwr, "upgrades": json.loads(row["upgrades"] or "{}"), "total_earned": nt, "prestige_mult": mult}
    conn.close()
    return jsonify(res)

@app.route('/api/rebirth/<chat_id>', methods=['POST'])
def rebirth(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT balance, total_earned, level, prestige_points, prestige_mult, total_prestiges FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    if not row: conn.close(); return jsonify({"error": "Player not found"}), 404
    
    lvl = row["level"] or 1
    te = row["total_earned"] or 0
    if lvl < 5 and te < 5000:
        conn.close(); return jsonify({"error": f"Нужен 5 уровень или 5000$ всего (сейчас: {lvl} / {te})"}), 400
        
    pp = row["prestige_points"] or 0
    gems_to_add = max(1, (te // 5000) - pp)
    new_total_gems = pp + gems_to_add
    new_mult = 1.0 + (new_total_gems * 0.05)
    new_prestiges = (row["total_prestiges"] or 0) + 1
    
    c.execute('''UPDATE players SET balance=0, clicks=0, level=1, passive_income=0, click_power=10, upgrades='{}', total_earned=0, last_update=?, prestige_points=?, prestige_mult=?, total_prestiges=? WHERE chat_id=?''',
              (time.time(), new_total_gems, new_mult, new_prestiges, chat_id))
    conn.commit(); conn.close()
    return jsonify({"success": True, "gems_added": gems_to_add, "total_gems": new_total_gems, "multiplier": new_mult, "message": f"Перерождение успешно! +{gems_to_add} 💎"})

@app.route('/api/shop', methods=['GET'])
def get_shop(): return jsonify(UPGRADES)

@app.route('/api/buy/<chat_id>/<upgrade_id>', methods=['POST'])
def buy_upgrade(chat_id, upgrade_id):
    if upgrade_id not in UPGRADES: return jsonify({"error": "Error"}), 400
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT balance, upgrades, click_power, passive_income FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    if not row: conn.close(); return jsonify({"error": "Not found"}), 404
    p = dict(row)
    p["upgrades"] = json.loads(p["upgrades"] or "{}")
    u = UPGRADES[upgrade_id]
    cnt = p["upgrades"].get(upgrade_id, 0)
    price = int(u["cost"] * (1.15 ** cnt))
    bal = p["balance"] or 0
    if bal < price: conn.close(); return jsonify({"error": "Мало денег"}), 400
    nb = bal - price
    nu = {**p["upgrades"], upgrade_id: cnt+1}
    npwr = (p["click_power"] or 10) + (u.get("power", 0) if u["type"]=="click" else 0)
    npass = (p["passive_income"] or 0) + (u.get("income", 0) if u["type"]=="passive" else 0)
    c.execute('UPDATE players SET balance=?, upgrades=?, click_power=?, passive_income=?, last_update=? WHERE chat_id=?', (nb, json.dumps(nu), npwr, npass, time.time(), chat_id))
    conn.commit(); conn.close()
    return jsonify({"balance": nb, "click_power": npwr, "passive_income": npass, "upgrades": nu, "success": True})

@app.route('/api/quests/<chat_id>', methods=['GET'])
def get_quests(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT quests_data FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone(); conn.close()
    if not row: return jsonify([])
    q_data = json.loads(row["quests_data"] or "{}")
    res = []
    for q in QUESTS:
        status = q_data.get(q["id"], {"progress":0, "claimed":False})
        res.append({**q, "progress": status["progress"], "claimed": status["claimed"]})
    return jsonify(res)

@app.route('/api/claim_quest/<chat_id>/<quest_id>', methods=['POST'])
def claim_quest(chat_id, quest_id):
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT quests_data, balance FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    if not row: conn.close(); return jsonify({"error": "Not found"}), 404
    q_data = json.loads(row["quests_data"] or "{}")
    if quest_id not in q_data or q_data[quest_id]["claimed"]: conn.close(); return jsonify({"error": "Already claimed"}), 400
    quest_def = next((q for q in QUESTS if q["id"] == quest_id), None)
    if not quest_def or q_data[quest_id]["progress"] < quest_def["target"]: conn.close(); return jsonify({"error": "Not ready"}), 400
    q_data[quest_id]["claimed"] = True
    nb = (row["balance"] or 0) + quest_def["reward"]
    c.execute('UPDATE players SET balance=?, quests_data=? WHERE chat_id=?', (nb, json.dumps(q_data), chat_id))
    conn.commit(); conn.close()
    return jsonify({"success": True, "balance": nb, "reward": quest_def["reward"]})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT chat_id, balance, level FROM players ORDER BY balance DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    return jsonify([{"rank":i+1, "chat_id":r["chat_id"], "balance":r["balance"], "level":r["level"]} for i,r in enumerate(rows)])

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
