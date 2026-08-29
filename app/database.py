import sqlite3
import os
from typing import Any, Dict

def get_db():
    """Получить соединение с БД"""
    db_url = os.environ.get('DATABASE_URL', '')
    
    if db_url:
        # PostgreSQL (на Render)
        import psycopg
        conn = psycopg.connect(db_url, row_factory=psycopg.rows.dict_row)
        return conn
    else:
        # SQLite (локально для тестов)
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

class Player:
    """Модель игрока"""
    
    @staticmethod
    def get_by_chat_id(conn, chat_id: str) -> Dict[str, Any]:
        """Получить игрока по chat_id"""
        c = conn.cursor()
        c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
        row = c.fetchone()
        
        if not row:
            # Создаём нового игрока
            ref_code = str(int(__import__('time').time()))[-6:]
            c.execute('''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, 
                upgrades, last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult, event_data)
                VALUES (?, 0, 0, 1, 0, 10, '{}', ?, '[]', 0, ?, '{}', 0, 1.0, '{}')''', 
                (chat_id, __import__('time').time(), ref_code))
            conn.commit()
            c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
            row = c.fetchone()
        
        player = dict(row) if row else {}
        player["upgrades"] = __import__('json').loads(player.get("upgrades") or "{}")
        player["achievements"] = __import__('json').loads(player.get("achievements") or "[]")
        player["event_data"] = __import__('json').loads(player.get("event_data") or "{}")
        
        conn.close()
        return player
    
    @staticmethod
    def process_click(conn, chat_id: str) -> Dict[str, Any]:
        """Обработать клик"""
        c = conn.cursor()
        c.execute('SELECT click_power, balance, clicks, upgrades, total_earned, prestige_mult FROM players WHERE chat_id = ?', (chat_id,))
        row = c.fetchone()
        
        if not row:
            ref_code = str(int(__import__('time').time()))[-6:]
            c.execute('''INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, upgrades, 
                last_update, achievements, total_earned, referral_code, quests_data, prestige_points, prestige_mult, event_data)
                VALUES (?, 10, 1, 1, 0, 10, '{}', ?, '[]', 10, ?, '{}', 0, 1.0, '{}')''', 
                (chat_id, __import__('time').time(), ref_code))
            conn.commit()
            return {"balance": 10, "clicks": 1, "level": 1, "click_power": 10, "upgrades": {}, "total_earned": 10, "prestige_mult": 1.0}
        else:
            rd = dict(row)
            pwr = rd.get("click_power") or 10
            mult = float(rd.get("prestige_mult") or 1.0)
            dmg = int(pwr * mult)
            
            nb = (rd.get("balance") or 0) + dmg
            nc = (rd.get("clicks") or 0) + 1
            nt = (rd.get("total_earned") or 0) + dmg
            
            c.execute('UPDATE players SET balance=?, clicks=?, total_earned=?, last_update=? WHERE chat_id=?', 
                     (nb, nc, nt, __import__('time').time(), chat_id))
            conn.commit()
            
            return {
                "balance": nb, "clicks": nc, "level": (nc//100)+1, "click_power": pwr,
                "upgrades": __import__('json').loads(rd.get("upgrades") or "{}"),
                "total_earned": nt, "prestige_mult": mult
            }
