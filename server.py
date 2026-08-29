from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, time, json, random
from datetime import datetime

app = Flask(__name__)
CORS(app)

USE_PG = bool(os.environ.get('DATABASE_URL'))
PARAM = '%s' if USE_PG else '?'

UPGRADES = {
    "shawarma": {"name": "Ларёк", "cost": 100, "income": 2, "icon": "\U0001F32F", "type": "passive"},
    "coffee": {"name": "Кофе", "cost": 500, "income": 10, "icon": "\u2615", "type": "passive"},
    "pizza": {"name": "Пиццерия", "cost": 1500, "income": 25, "icon": "\U0001F355", "type": "passive"},
    "office": {"name": "Офис", "cost": 3000, "income": 60, "icon": "\U0001F3E2", "type": "passive"},
    "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "\U0001F3ED", "type": "passive"},
    "taxi": {"name": "Такси", "cost": 20000, "income": 450, "icon": "\U0001F695", "type": "passive"},
    "bank": {"name": "Банк", "cost": 80000, "income": 1500, "icon": "\U0001F3E6", "type": "passive"},
    "mall": {"name": "ТЦ", "cost": 150000, "income": 3000, "icon": "\U0001F6CD\uFE0F", "type": "passive"},
    "tech_park": {"name": "IT Парк", "cost": 500000, "income": 8000, "icon": "\U0001F4BB", "type": "passive"},
    "spaceport": {"name": "Космопорт", "cost": 2000000, "income": 25000, "icon": "\U0001F680", "type": "passive"},
    "mouse": {"name": "Золотая мышь", "cost": 200, "power": 5, "icon": "\U0001F5B1\uFE0F", "type": "click"},
    "ai_bot": {"name": "AI-Бот", "cost": 1000, "power": 25, "icon": "\U0001F916", "type": "click"},
    "exosuit": {"name": "Экзоскелет", "cost": 5000, "power": 100, "icon": "\U0001F4AA", "type": "click"},
    "quantum": {"name": "Квантовый палец", "cost": 50000, "power": 500, "icon": "\u26A1", "type": "click"}
}

ACHIEVEMENTS = [
    {"id": "click_10", "name": "Первый шаг", "desc": "10 кликов", "target": 10, "type": "clicks", "reward": 50, "rarity": "common"},
    {"id": "click_100", "name": "Кликер", "desc": "100 кликов", "target": 100, "type": "clicks", "reward": 200, "rarity": "common"},
    {"id": "click_1000", "name": "Тап-мастер", "desc": "1000 кликов", "target": 1000, "type": "clicks", "reward": 1000, "rarity": "uncommon"},
    {"id": "earn_100", "name": "Старт", "desc": "100$ всего", "target": 100, "type": "total_earned", "reward": 100, "rarity": "common"},
    {"id": "earn_1000", "name": "Магнат", "desc": "1000$ всего", "target": 1000, "type": "total_earned", "reward": 500, "rarity": "common"},
    {"id": "earn_10000", "name": "Богач", "desc": "10000$ всего", "target": 10000, "type": "total_earned", "reward": 2500, "rarity": "uncommon"},
    {"id": "first_business", "name": "Предприниматель", "desc": "Первый бизнес", "target": 1, "type": "upgrades_count", "reward": 100, "rarity": "common"},
    {"id": "ten_upgrades", "name": "Инвестор", "desc": "10 улучшений", "target": 10, "type": "upgrades_count", "reward": 500, "rarity": "uncommon"},
    {"id": "rebirth_1", "name": "Новая жизнь", "desc": "1 перерождение", "target": 1, "type": "prestiges", "reward": 1000, "rarity": "rare"}
]

EVENTS = [
    {"id": "crisis", "name": "Кризис", "desc": "Доход -50%", "duration": 300, "effect": {"passive_mult": 0.5, "click_mult": 0.5}, "color": "#ef4444"},
    {"id": "boom", "name": "Бум", "desc": "Доход x2", "duration": 180, "effect": {"passive_mult": 2.0, "click_mult": 2.0}, "color": "#10b981"},
    {"id": "investment", "name": "Инвестиции", "desc": "Бонус $100/сек", "duration": 120, "effect": {"bonus_per_sec": 100}, "color": "#f59e0b"},
    {"id": "competitor", "name": "Конкурент", "desc": "Клики отключены", "duration": 60, "effect": {"click_disabled": True}, "color": "#8b5cf6"}
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
    c.execute(f'''CREATE TABLE IF NOT EXISTS players (
        chat_id TEXT PRIMARY KEY, balance INTEGER DEFAULT 0, clicks INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1, passive_income INTEGER DEFAULT 0, click_power INTEGER DEFAULT 10,
        upgrades TEXT DEFAULT '{{}}', last_update REAL DEFAULT 0, achievements TEXT DEFAULT '[]',
        total_earned INTEGER DEFAULT 0, referral_code TEXT DEFAULT '', referred_by TEXT DEFAULT '',
        referral_earnings INTEGER DEFAULT 0, quests_data TEXT DEFAULT '{{}}',
        prestige_points INTEGER DEFAULT 0, prestige_mult REAL DEFAULT 1.0, total_prestiges INTEGER DEFAULT 0,
        event_data TEXT DEFAULT '{{}}'
    )''')
    
    c.execute(f'''CREATE TABLE IF NOT EXISTS boss (
        id INTEGER PRIMARY KEY, 
        name TEXT DEFAULT 'Огненный Дракон', 
        hp INTEGER DEFAULT 10000, 
        max_hp INTEGER DEFAULT 10000, 
        level INTEGER DEFAULT 1, 
        status TEXT DEFAULT 'active'
    )''')
    
    try:
        c.execute(f"INSERT INTO boss (id, name, hp, max_hp, level, status) VALUES (1, 'Огненный Дракон', 10000, 10000, 1, 'active') ON CONFLICT (id) DO NOTHING")
    except:
        pass
    
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
            upgrades, last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult, event_data)
            VALUES ({PARAM}, 0, 0, 1, 0, 10, '{{}}', {PARAM}, '[]', 0, {PARAM}, '{{}}', 0, 1.0, '{{}}')''', (chat_id, time.time(), ref_code))
        conn.commit()
        c.execute(f'SELECT * FROM players WHERE chat_id = {PARAM}', (chat_id,))
        row = c.fetchone()
    
    player = dict(row) if row else {}
    player["upgrades"] = json.loads(player.get("upgrades") or "{}")
    player["achievements"] = json.loads(player.get("achievements") or "[]")
    player["event_data"] = json.loads(player.get("event_data") or "{}")
    
    now = time.time(); mult = float(player.get("prestige_mult") or 1.0)
    
    # Проверка и выдача достижений
    new_achievements = check_and_grant_achievements(player, c, chat_id)
    
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
    player["prestige_points"] = player.get("prestige_points") or 0
    player["total_prestiges"] = player.get("total_prestiges") or 0
    return jsonify({**player, "new_achievements": new_achievements})

def check_and_grant_achievements(player, cursor, chat_id):
    """Проверяет и выдает новые достижения"""
    achieved_ids = [a["id"] for a in player.get("achievements", [])]
    new_achs = []
    
    for ach in ACHIEVEMENTS:
        if ach["id"] in achieved_ids:
            continue
        
        # Получаем текущее значение
        val = 0
        if ach["type"] == "clicks":
            val = player.get("clicks", 0)
        elif ach["type"] == "total_earned":
            val = player.get("total_earned", 0)
        elif ach["type"] == "upgrades_count":
            val = sum(player.get("upgrades", {}).values())
        elif ach["type"] == "prestiges":
            val = player.get("total_prestiges", 0)
        
        # Если достигли цели
        if val >= ach["target"]:
            new_achs.append(ach)
            player["achievements"].append(ach)
            player["balance"] += ach["reward"]
            
            # Сохраняем в БД
            cursor.execute(f'UPDATE players SET achievements = {PARAM}, balance = {PARAM} WHERE chat_id = {PARAM}',
                          (json.dumps(player["achievements"]), player["balance"], chat_id))
    
    return new_achs

@app.route('/api/click/<chat_id>', methods=['POST'])
def click(chat_id):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute(f'SELECT click_power, balance, clicks, upgrades, total_earned, prestige_mult, event_data, achievements FROM players WHERE chat_id = {PARAM}', (chat_id,))
        row = c.fetchone()
        
        pwr, mult, dmg = 10, 1.0, 10
        event_data = {}
        if row:
            rd = dict(row)
            pwr = rd.get("click_power") or 10
            mult = float(rd.get("prestige_mult") or 1.0)
            event_data = json.loads(rd.get("event_data") or "{}")
            dmg = int(pwr * mult)
        
        now = time.time()
        if event_data.get("end_time", 0) > now:
            cur_ev = next((e for e in EVENTS if e["id"] == event_data["event_id"]), None)
            if cur_ev and cur_ev["effect"].get("click_disabled"):
                conn.close()
                return jsonify({"error": "Конкуренты мешают кликать!"}), 400
        
        boss_dmg = int(dmg * 0.5) 
        c.execute("UPDATE boss SET hp = hp - %s WHERE id = 1 AND status = 'active'", (boss_dmg,))
        
        if not row:
            ref_code = str(int(time.time()))[-6:]
            c.execute(f'''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, upgrades, 
                last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult, event_data)
                VALUES ({PARAM}, 10, 1, 1, 0, 10, '{{}}', {PARAM}, '[]', 10, {PARAM}, '{{}}', 0, 1.0, '{{}}')''', (chat_id, time.time(), ref_code))
            conn.commit()
            res = {"balance": 10, "clicks": 1, "level": 1, "click_power": pwr, "upgrades": {}, "total_earned": 10, "prestige_mult": mult, "boss_dmg": boss_dmg, "new_achievements": []}
        else:
            nb = (rd.get("balance") or 0) + dmg
            nc = (rd.get("clicks") or 0) + 1; nt = (rd.get("total_earned") or 0) + dmg
            c.execute(f'UPDATE players SET balance={PARAM}, clicks={PARAM}, total_earned={PARAM}, last_update={PARAM} WHERE chat_id={PARAM}', (nb, nc, nt, time.time(), chat_id))
            conn.commit()
            
            # Проверяем достижения после клика
            rd["balance"] = nb; rd["clicks"] = nc; rd["total_earned"] = nt
            new_achs = check_and_grant_achievements(rd, c, chat_id)
            
            res = {"balance": nb, "clicks": nc, "level": (nc//100)+1, "click_power": pwr, "upgrades": json.loads(rd.get("upgrades") or "{}"), "total_earned": nt, "prestige_mult": mult, "boss_dmg": boss_dmg, "new_achievements": new_achs}
        
        c.execute("SELECT hp, max_hp, level FROM boss WHERE id = 1")
        boss_row = c.fetchone()
        if boss_row["hp"] <= 0:
            reward = boss_row["max_hp"] * 2
            new_level = boss_row["level"] + 1
            new_max_hp = int(boss_row["max_hp"] * 1.5)
            c.execute("UPDATE boss SET hp = %s, max_hp = %s, level = %s WHERE id = 1", (new_max_hp, new_max_hp, new_level))
            conn.commit()
            res["boss_killed"] = {"level": new_level, "reward": reward}
        else:
            res["boss"] = {"hp": boss_row["hp"], "max_hp": boss_row["max_hp"], "level": boss_row["level"]}

        conn.close()
        return jsonify(res)
    except Exception as e:
        print(f"CLICK ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/shop', methods=['GET'])
def get_shop(): return jsonify(UPGRADES)

@app.route('/api/buy/<chat_id>/<upgrade_id>', methods=['POST'])
def buy_upgrade(chat_id, upgrade_id):
    if upgrade_id not in UPGRADES: return jsonify({"error": "Invalid"}), 400
    conn = get_db(); c = conn.cursor()
    c.execute(f'SELECT balance, upgrades, click_power, passive_income, achievements FROM players WHERE chat_id = {PARAM}', (chat_id,))
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
    conn.commit()
    
    # Проверяем достижения после покупки
    p["balance"] = nb; p["upgrades"] = nu
    new_achs = check_and_grant_achievements(p, c, chat_id)
    
    conn.close()
    return jsonify({"balance": nb, "click_power": npwr, "passive_income": npass, "upgrades": nu, "success": True, "new_achievements": new_achs})

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
    row = c.fetchone(); conn.close()
    if row: return jsonify({"hp": row["hp"], "max_hp": row["max_hp"], "level": row["level"], "name": row["name"]})
    return jsonify({"error": "No boss"}), 404

@app.route('/api/achievements', methods=['GET'])
def get_achievements(): return jsonify(ACHIEVEMENTS)

@app.route('/api/events/start/<chat_id>', methods=['POST'])
def start_event(chat_id):
    event = random.choice(EVENTS)
    end_time = time.time() + event["duration"]
    conn = get_db(); c = conn.cursor()
    c.execute(f'UPDATE players SET event_data = {PARAM} WHERE chat_id = {PARAM}', 
              (json.dumps({"event_id": event["id"], "end_time": end_time}), chat_id))
    conn.commit(); conn.close()
    return jsonify({"success": True, "event": event, "end_time": end_time})

@app.route('/api/events/status/<chat_id>', methods=['GET'])
def event_status(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute(f'SELECT event_data FROM players WHERE chat_id = {PARAM}', (chat_id,))
    row = c.fetchone(); conn.close()
    if not row: return jsonify({"active": False})
    event_data = json.loads(row["event_data"] or "{}")
    now = time.time()
    if event_data.get("end_time", 0) <= now: return jsonify({"active": False})
    active_event = next((e for e in EVENTS if e["id"] == event_data["event_id"]), None)
    if active_event: return jsonify({"active": True, "event": active_event, "remaining": int(event_data["end_time"] - now)})
    return jsonify({"active": False})

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
