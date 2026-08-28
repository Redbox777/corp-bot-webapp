from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, time, json
from datetime import datetime

app = Flask(__name__)
CORS(app)

USE_PG = bool(os.environ.get('DATABASE_URL'))
PARAM = '%s' if USE_PG else '?'

UPGRADES = {
    "shawarma": {"name": "Ларёк", "cost": 100, "income": 2, "icon": "\U0001F32F", "type": "passive"},
    "coffee": {"name": "Кофе", "cost": 500, "income": 10, "icon": "\u2615", "type": "passive"},
    "office": {"name": "Офис", "cost": 2000, "income": 50, "icon": "\U0001F3E2", "type": "passive"},
    "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "\U0001F3ED", "type": "passive"},
    "bank": {"name": "Банк", "cost": 50000, "income": 1500, "icon": "\U0001F3E6", "type": "passive"},
    "mouse": {"name": "Золотая мышь", "cost": 200, "power": 5, "icon": "\U0001F5B1\uFE0F", "type": "click"},
    "ai_bot": {"name": "AI-Бот", "cost": 1000, "power": 25, "icon": "\U0001F916", "type": "click"},
    "quantum": {"name": "Квантовый ПК", "cost": 100000, "power": 500, "icon": "\U0001F4BB", "type": "click"}
}

QUESTS = [
    {"id": "click_100", "name": "Кликер", "desc": "100 кликов", "target": 100, "type": "clicks", "reward": 200, "daily": True},
    {"id": "earn_1000", "name": "Магнат", "desc": "1000$ всего", "target": 1000, "type": "total_earned", "reward": 500, "daily": True},
    {"id": "rebirth_1", "name": "Новая жизнь", "desc": "1 перерождение", "target": 1, "type": "prestiges", "reward": 1000, "daily": False}
]

def get_db():
    if USE_PG:
        import psycopg
        conn = psycopg.connect(os.environ['DATABASE_URL'], row_factory=psycopg.rows.dict_row)
        return conn
    else:
        import sqlite3
        conn = sqlite3.connect('players.db', timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Таблица игроков
    c.execute(f'''CREATE TABLE IF NOT EXISTS players (
        chat_id TEXT PRIMARY KEY, balance INTEGER DEFAULT 0, clicks INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1, passive_income INTEGER DEFAULT 0, click_power INTEGER DEFAULT 10,
        upgrades TEXT DEFAULT '{{}}', last_update REAL DEFAULT 0, achievements TEXT DEFAULT '[]',
        total_earned INTEGER DEFAULT 0, referral_code TEXT DEFAULT '', referred_by TEXT DEFAULT '',
        referral_earnings INTEGER DEFAULT 0, quests_data TEXT DEFAULT '{{}}',
        prestige_points INTEGER DEFAULT 0, prestige_mult REAL DEFAULT 1.0, total_prestiges INTEGER DEFAULT 0
    )''')
    # Таблица Босса (Общая для всех)
    c.execute(f'''CREATE TABLE IF NOT EXISTS boss (
        id INTEGER PRIMARY KEY CHECK (id = 1), 
        name TEXT DEFAULT 'Огненный Дракон', hp INTEGER DEFAULT 10000, max_hp INTEGER DEFAULT 10000, 
        level INTEGER DEFAULT 1, status TEXT DEFAULT 'active'
    )''')
    # Вставляем босса если нет
    c.execute(f"INSERT INTO boss (id, name, hp, max_hp, level) VALUES (1, 'Огненный Дракон', 10000, 10000, 1) ON CONFLICT (id) DO NOTHING")
    conn.commit()
    conn.close()

@app.route('/')
def index(): return send_from_directory('.', 'index.html')

@app.route('/api/player/<chat_id>', methods=['GET'])
def get_player(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute(f'SELECT * FROM players WHERE chat_id = {PARAM}', (chat_id,))
    row = c.fetchone()
    if not row:
        ref_code = str(int(time.time()))[-6:]
        c.execute(f'''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, 
            upgrades, last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult)
            VALUES ({PARAM}, 0, 0, 1, 0, 10, '{{}}', {PARAM}, '[]', 0, {PARAM}, '{{}}', 0, 1.0)''', (chat_id, time.time(), ref_code))
        conn.commit()
        c.execute(f'SELECT * FROM players WHERE chat_id = {PARAM}', (chat_id,))
        row = c.fetchone()
    
    player = dict(row) if row else {}
    player["upgrades"] = json.loads(player.get("upgrades") or "{}")
    player["achievements"] = json.loads(player.get("achievements") or "[]")
    raw_q = player.get("quests_data")
    q_data = json.loads(raw_q) if isinstance(raw_q, str) and raw_q else (raw_q if isinstance(raw_q, dict) else {})
    
    today = datetime.now().strftime("%Y-%m-%d")
    for q in QUESTS:
        if q["id"] not in q_data: q_data[q["id"]] = {"progress": 0, "claimed": False, "last_date": today}
        if q["daily"] and q_data[q["id"]]["last_date"] != today: q_data[q["id"]] = {"progress": 0, "claimed": False, "last_date": today}
        val = {"clicks": player.get("clicks",0), "total_earned": player.get("total_earned",0),
               "upgrades_count": sum(player.get("upgrades",{}).values()), "level": player.get("level",1),
               "prestiges": player.get("total_prestiges",0)}.get(q["type"], 0)
        q_data[q["id"]]["progress"] = min(val, q["target"])
    
    c.execute(f"UPDATE players SET quests_data = {PARAM} WHERE chat_id = {PARAM}", (json.dumps(q_data), chat_id))
    
    now = time.time(); mult = float(player.get("prestige_mult") or 1.0)
    if player.get("last_update") and player.get("passive_income", 0) > 0:
        sec = now - player["last_update"]
        if sec > 1:
            earned = int(player["passive_income"] * sec * mult)
            player["balance"] += earned; player["total_earned"] += earned
            if player.get("referred_by"):
                bonus = int(earned * 0.01)
                if bonus > 0: c.execute(f'UPDATE players SET balance = balance + {PARAM} WHERE chat_id = {PARAM}', (bonus, player["referred_by"]))
            c.execute(f'UPDATE players SET balance = {PARAM}, total_earned = {PARAM}, last_update = {PARAM} WHERE chat_id = {PARAM}', (player["balance"], player["total_earned"], now, chat_id))
    
    conn.commit(); conn.close()
    player["quests_data"] = q_data
    player["prestige_points"] = player.get("prestige_points") or 0
    player["prestige_mult"] = mult
    player["total_prestiges"] = player.get("total_prestiges") or 0
    return jsonify(player)

@app.route('/api/click/<chat_id>', methods=['POST'])
def click(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute(f'SELECT click_power, balance, clicks, upgrades, total_earned, prestige_mult FROM players WHERE chat_id = {PARAM}', (chat_id,))
    row = c.fetchone()
    
    pwr, mult, dmg = 10, 1.0, 10
    if row:
        rd = dict(row)
        pwr = rd.get("click_power") or 10
        mult = float(rd.get("prestige_mult") or 1.0)
        dmg = int(pwr * mult)
    
    # Урон боссу (пассивный доход тоже бьет, но медленнее)
    boss_dmg = int(dmg * 0.5) 
    c.execute("UPDATE boss SET hp = hp - ? WHERE id = 1 AND status = 'active'", (boss_dmg,))
    
    if not row:
        ref_code = str(int(time.time()))[-6:]
        c.execute(f'''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, upgrades, 
            last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult)
            VALUES ({PARAM}, 10, 1, 1, 0, 10, '{{}}', {PARAM}, '[]', 10, {PARAM}, '{{}}', 0, 1.0)''', (chat_id, time.time(), ref_code))
        conn.commit()
        res = {"balance": 10, "clicks": 1, "level": 1, "click_power": pwr, "upgrades": {}, "total_earned": 10, "prestige_mult": mult, "boss_dmg": boss_dmg}
    else:
        nb = (rd.get("balance") or 0) + dmg
        nc = (rd.get("clicks") or 0) + 1; nt = (rd.get("total_earned") or 0) + dmg
        c.execute(f'UPDATE players SET balance={PARAM}, clicks={PARAM}, total_earned={PARAM}, last_update={PARAM} WHERE chat_id={PARAM}', (nb, nc, nt, time.time(), chat_id))
        conn.commit()
        res = {"balance": nb, "clicks": nc, "level": (nc//100)+1, "click_power": pwr, "upgrades": json.loads(rd.get("upgrades") or "{}"), "total_earned": nt, "prestige_mult": mult, "boss_dmg": boss_dmg}
    
    # Проверка убийства босса
    c.execute("SELECT hp, max_hp, level FROM boss WHERE id = 1")
    boss_row = c.fetchone()
    boss_hp = boss_row["hp"]
    
    if boss_hp <= 0:
        reward = boss_row["max_hp"] * 2
        new_level = boss_row["level"] + 1
        new_max_hp = int(boss_row["max_hp"] * 1.5)
        c.execute("UPDATE boss SET hp = ?, max_hp = ?, level = ? WHERE id = 1", (new_max_hp, new_max_hp, new_level))
        conn.commit()
        res["boss_killed"] = {"level": new_level, "reward": reward}
    else:
        res["boss"] = {"hp": boss_hp, "max_hp": boss_row["max_hp"], "level": boss_row["level"]}

    conn.close()
    return jsonify(res)

@app.route('/api/shop', methods=['GET'])
def get_shop(): return jsonify(UPGRADES)

@app.route('/api/buy/<chat_id>/<upgrade_id>', methods=['POST'])
def buy_upgrade(chat_id, upgrade_id):
    if upgrade_id not in UPGRADES: return jsonify({"error": "Invalid"}), 400
    conn = get_db(); c = conn.cursor()
    c.execute(f'SELECT balance, upgrades, click_power, passive_income FROM players WHERE chat_id = {PARAM}', (chat_id,))
    row = c.fetchone()
    if not row: conn.close(); return jsonify({"error": "Not found"}), 404
    p = dict(row); p["upgrades"] = json.loads(p["upgrades"] or "{}")
    u = UPGRADES[upgrade_id]; cnt = p["upgrades"].get(upgrade_id, 0)
    price = int(u["cost"] * (1.15 ** cnt)); bal = p["balance"] or 0
    if bal < price: conn.close(); return jsonify({"error": "Мало денег"}), 400
    nb = bal - price; nu = {**p["upgrades"], upgrade_id: cnt+1}
    npwr = (p["click_power"] or 10) + (u.get("power", 0) if u["type"]=="click" else 0)
    npass = (p["passive_income"] or 0) + (u.get("income", 0) if u["type"]=="passive" else 0)
    c.execute(f'UPDATE players SET balance={PARAM}, upgrades={PARAM}, click_power={PARAM}, passive_income={PARAM}, last_update={PARAM} WHERE chat_id={PARAM}', (nb, json.dumps(nu), npwr, npass, time.time(), chat_id))
    conn.commit(); conn.close()
    return jsonify({"balance": nb, "click_power": npwr, "passive_income": npass, "upgrades": nu, "success": True})

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT chat_id, balance, level FROM players ORDER BY balance DESC LIMIT 50')
    rows = c.fetchall(); conn.close()
    return jsonify([{"rank": i+1, "chat_id": r["chat_id"], "balance": r["balance"], "level": r["level"]} for i, r in enumerate(rows)])

@app.route('/api/boss_status', methods=['GET'])
def boss_status():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT hp, max_hp, level, name FROM boss WHERE id = 1")
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({"hp": row["hp"], "max_hp": row["max_hp"], "level": row["level"], "name": row["name"]})
    return jsonify({"error": "No boss"}), 404

@app.route('/api/quests/<chat_id>', methods=['GET'])
def get_quests(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute(f'SELECT quests_data FROM players WHERE chat_id = {PARAM}', (chat_id,))
    row = c.fetchone(); conn.close()
    if not row: return jsonify([])
    raw = row["quests_data"] if isinstance(row, dict) else row[0]
    qd = json.loads(raw) if isinstance(raw, str) and raw else (raw if isinstance(raw, dict) else {})
    return jsonify([{**q, "progress": qd.get(q["id"], {}).get("progress", 0), "claimed": qd.get(q["id"], {}).get("claimed", False)} for q in QUESTS])

@app.route('/api/claim_quest/<chat_id>/<quest_id>', methods=['POST'])
def claim_quest(chat_id, quest_id):
    conn = get_db(); c = conn.cursor()
    c.execute(f'SELECT quests_data, balance FROM players WHERE chat_id = {PARAM}', (chat_id,))
    row = c.fetchone()
    if not row: conn.close(); return jsonify({"error": "Not found"}), 404
    rd = dict(row); raw = rd.get("quests_data")
    qd = json.loads(raw) if isinstance(raw, str) and raw else (raw if isinstance(raw, dict) else {})
    if quest_id not in qd or qd[quest_id]["claimed"]: conn.close(); return jsonify({"error": "Already claimed"}), 400
    q = next((x for x in QUESTS if x["id"] == quest_id), None)
    if not q or qd[quest_id]["progress"] < q["target"]: conn.close(); return jsonify({"error": "Not ready"}), 400
    qd[quest_id]["claimed"] = True; nb = (rd.get("balance") or 0) + q["reward"]
    c.execute(f'UPDATE players SET balance={PARAM}, quests_data={PARAM} WHERE chat_id={PARAM}', (nb, json.dumps(qd), chat_id))
    conn.commit(); conn.close()
    return jsonify({"success": True, "balance": nb, "reward": q["reward"]})

@app.route('/api/rebirth/<chat_id>', methods=['POST'])
def rebirth(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute(f'SELECT balance, total_earned, level, prestige_points, prestige_mult, total_prestiges FROM players WHERE chat_id = {PARAM}', (chat_id,))
    row = c.fetchone()
    if not row: conn.close(); return jsonify({"error": "Not found"}), 404
    rd = dict(row)
    lvl = rd.get("level") or 1; te = rd.get("total_earned") or 0
    if lvl < 5 and te < 5000: conn.close(); return jsonify({"error": f"Нужен 5 ур. или 5000$ (сейчас: {lvl}/{te})"}), 400
    pp = rd.get("prestige_points") or 0; gems = max(1, (te // 5000) - pp)
    ng = pp + gems; nm = 1.0 + (ng * 0.05); np = (rd.get("total_prestiges") or 0) + 1
    c.execute(f'''UPDATE players SET balance=0, clicks=0, level=1, passive_income=0, click_power=10, upgrades='{{}}',
        total_earned=0, last_update={PARAM}, prestige_points={PARAM}, prestige_mult={PARAM}, total_prestiges={PARAM} WHERE chat_id={PARAM}''',
        (time.time(), ng, nm, np, chat_id))
    conn.commit(); conn.close()
    return jsonify({"success": True, "gems_added": gems, "total_gems": ng, "multiplier": nm, "message": f"+{gems} 💎"})

@app.route('/api/referral_link/<chat_id>', methods=['GET'])
def get_ref_link(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute(f'SELECT referral_code FROM players WHERE chat_id = {PARAM}', (chat_id,))
    row = c.fetchone(); conn.close()
    if not row: return jsonify({"error": "Not found"}), 404
    bot = request.args.get('bot', 'MagnatZeroBot')
    return jsonify({"link": f"https://t.me/{bot}?start=ref_{row['referral_code']}", "code": row["referral_code"]})

@app.route('/api/bind_referral/<chat_id>/<ref_code>', methods=['POST'])
def bind_ref(chat_id, ref_code):
    conn = get_db(); c = conn.cursor()
    c.execute(f'SELECT referred_by FROM players WHERE chat_id = {PARAM}', (chat_id,))
    row = c.fetchone()
    if not row or row["referred_by"]: conn.close(); return jsonify({"error": "Already bound"}), 400
    c.execute(f'SELECT chat_id FROM players WHERE referral_code = {PARAM}', (ref_code,))
    ref = c.fetchone()
    if not ref or ref["chat_id"] == chat_id: conn.close(); return jsonify({"error": "Invalid"}), 400
    c.execute(f'UPDATE players SET referred_by = {PARAM} WHERE chat_id = {PARAM}', (ref["chat_id"], chat_id))
    c.execute(f'UPDATE players SET balance = balance + 500 WHERE chat_id IN ({PARAM}, {PARAM})', (ref["chat_id"], chat_id))
    conn.commit(); conn.close()
    return jsonify({"success": True, "bonus": 500})

init_db()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
