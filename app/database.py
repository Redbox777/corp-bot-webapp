import sqlite3
import os
import json
import time
from typing import Any, Dict, Optional
from app.utils.cache import cache_get, cache_set, cache_delete

def get_db():
    """Получить соединение с БД"""
    db_url = os.environ.get('DATABASE_URL', '')
    
    if db_url:
        import psycopg
        conn = psycopg.connect(db_url, row_factory=psycopg.rows.dict_row)
        return conn
    else:
        conn = sqlite3.connect('players.db', timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Инициализация БД"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        chat_id TEXT PRIMARY KEY, balance INTEGER DEFAULT 0, clicks INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1, passive_income INTEGER DEFAULT 0, click_power INTEGER DEFAULT 10,
        upgrades TEXT DEFAULT '{}', last_update REAL DEFAULT 0, achievements TEXT DEFAULT '[]',
        total_earned INTEGER DEFAULT 0, referral_code TEXT DEFAULT '', referred_by TEXT DEFAULT '',
        referral_earnings INTEGER DEFAULT 0, quests_data TEXT DEFAULT '{}',
        prestige_points INTEGER DEFAULT 0, prestige_mult REAL DEFAULT 1.0, total_prestiges INTEGER DEFAULT 0,
        event_data TEXT DEFAULT '{}'
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS boss (
        id INTEGER PRIMARY KEY, 
        name TEXT DEFAULT 'Огненный Дракон', 
        hp INTEGER DEFAULT 10000, 
        max_hp INTEGER DEFAULT 10000, 
        level INTEGER DEFAULT 1, 
        status TEXT DEFAULT 'active'
    )''')
    
    try:
        c.execute("INSERT INTO boss (id, name, hp, max_hp, level, status) VALUES (1, 'Огненный Дракон', 10000, 10000, 1, 'active') ON CONFLICT (id) DO NOTHING")
    except:
        pass
    
    conn.commit()
    conn.close()

def get_player_data(chat_id: str):
    """
    Получить данные игрока (С ИСПРАВЛЕННЫМ КЭШЕМ)
    Гарантирует что кэш содержит полные данные
    """
    conn = get_db()
    c = conn.cursor()
    
    # Проверяем есть ли игрок
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        # Создаём нового игрока
        ref_code = str(int(time.time()))[-6:]
        now = time.time()
        c.execute('''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, 
            upgrades, last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult, event_data)
            VALUES (?, 0, 0, 1, 0, 10, '{}', ?, '[]', 0, ?, '{}', 0, 1.0, '{}')''', 
            (chat_id, now, ref_code))
        conn.commit()
        
        # СРАЗУ перечитываем чтобы получить полные данные
        c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
        row = c.fetchone()
    
    player = dict(row) if row else {}
    
    # Парсим JSON поля
    try:
        player["upgrades"] = json.loads(player.get("upgrades") or "{}")
        player["achievements"] = json.loads(player.get("achievements") or "[]")
        player["event_data"] = json.loads(player.get("event_data") or "{}")
        player["quests_data"] = json.loads(player.get("quests_data") or "{}")
    except:
        # Если ошибка парсинга — используем дефолтные значения
        player["upgrades"] = {}
        player["achievements"] = []
        player["event_data"] = {}
        player["quests_data"] = {}
    
    # Кэшируем ТОЛЬКО полные данные
    cache_key = f"player:{chat_id}"
    cache_set(cache_key, player, ttl=60)  # Уменьшили TTL до 60 сек для свежести
    
    conn.close()
    return player

def process_click(chat_id: str):
    """
    Обработать клик (Атомарное обновление)
    """
    conn = get_db()
    c = conn.cursor()
    
    # Получаем текущую силу клика
    c.execute('SELECT click_power, prestige_mult FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row:
        # Если игрока нет — создаём
        ref_code = str(int(time.time()))[-6:]
        now = time.time()
        c.execute('''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, upgrades, 
            last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult, event_data)
            VALUES (?, 10, 1, 1, 0, 10, '{}', ?, '[]', 10, ?, '{}', 0, 1.0, '{}')''', 
            (chat_id, now, ref_code))
        conn.commit()
        conn.close()
        return {"balance": 10, "clicks": 1, "level": 1, "click_power": 10, "upgrades": {}, "total_earned": 10, "prestige_mult": 1.0}
    
    rd = dict(row)
    pwr = rd.get("click_power") or 10
    mult = float(rd.get("prestige_mult") or 1.0)
    dmg = int(pwr * mult)
    
    # АТОМАРНОЕ обновление (защищено от гонок)
    c.execute('''UPDATE players 
                 SET balance = balance + ?, 
                     clicks = clicks + 1, 
                     total_earned = total_earned + ?, 
                     last_update = ? 
                 WHERE chat_id = ?''', 
             (dmg, dmg, time.time(), chat_id))
    conn.commit()
    
    # СРАЗУ перечитываем актуальный баланс
    c.execute('SELECT balance, clicks, total_earned FROM players WHERE chat_id = ?', (chat_id,))
    final_row = c.fetchone()
    
    result = {
        "balance": final_row["balance"],
        "clicks": final_row["clicks"],
        "level": (final_row["clicks"] // 100) + 1,
        "click_power": pwr,
        "upgrades": {},  # Упрощаем ответ
        "total_earned": final_row["total_earned"],
        "prestige_mult": mult
    }
    
    # Инвалидируем кэш
    cache_delete(f"player:{chat_id}")
    
    conn.close()
    return result
