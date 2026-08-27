import sqlite3
from config import config

def get_connection():
    """Получить соединение с БД"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Инициализация базы данных"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS players (
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
        referral_earnings INTEGER DEFAULT 0,
        quests_data TEXT DEFAULT '{}',
        prestige_points INTEGER DEFAULT 0,
        prestige_mult REAL DEFAULT 1.0,
        total_prestiges INTEGER DEFAULT 0
    )''')
    
    # Безопасное добавление новых колонок
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
        except Exception as e:
            print(f"Warning: Could not add column {col}: {e}")
    
    conn.commit()
    conn.close()

def create_player(chat_id, ref_code):
    """Создать нового игрока"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO players (chat_id, balance, clicks, level, passive_income, click_power, 
                            upgrades, last_update, achievements, total_earned, referral_code, 
                            quests_data, prestige_points, prestige_mult)
        VALUES (?, 0, 0, 1, 0, 10, '{}', ?, '[]', 0, ?, '{}', 0, 1.0)
    ''', (chat_id, __import__('time').time(), ref_code))
    conn.commit()
    conn.close()

def get_player(chat_id):
    """Получить игрока по ID"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_player(chat_id, **kwargs):
    """Обновить данные игрока"""
    if not kwargs:
        return
    
    conn = get_connection()
    c = conn.cursor()
    set_clause = ', '.join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [chat_id]
    c.execute(f'UPDATE players SET {set_clause} WHERE chat_id = ?', values)
    conn.commit()
    conn.close()
