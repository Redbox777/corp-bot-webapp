from flask import Blueprint, jsonify
from app.database import get_db
import json
import time
import random

events_bp = Blueprint('events', __name__)

EVENTS = [
    {"id": "crisis", "name": "Кризис", "desc": "Доход -50%", "duration": 300, "effect": {"passive_mult": 0.5, "click_mult": 0.5}, "color": "#ef4444"},
    {"id": "boom", "name": "Бум", "desc": "Доход x2", "duration": 180, "effect": {"passive_mult": 2.0, "click_mult": 2.0}, "color": "#10b981"},
    {"id": "investment", "name": "Инвестиции", "desc": "Бонус $100/сек", "duration": 120, "effect": {"bonus_per_sec": 100}, "color": "#f59e0b"},
    {"id": "competitor", "name": "Конкурент", "desc": "Клики отключены", "duration": 60, "effect": {"click_disabled": True}, "color": "#8b5cf6"}
]

@events_bp.route('/events/start/<chat_id>', methods=['POST'])
def start_event(chat_id):
    """Запустить случайное событие"""
    event = random.choice(EVENTS)
    end_time = time.time() + event["duration"]
    
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE players SET event_data = ? WHERE chat_id = ?',
              (json.dumps({"event_id": event["id"], "end_time": end_time}), chat_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "event": event, "end_time": end_time})

@events_bp.route('/events/status/<chat_id>', methods=['GET'])
def event_status(chat_id):
    """Получить статус активного события"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT event_data FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"active": False})
    
    event_data = json.loads(row["event_data"] or "{}")
    now = time.time()
    
    if event_data.get("end_time", 0) <= now:
        return jsonify({"active": False})
    
    active_event = next((e for e in EVENTS if e["id"] == event_data["event_id"]), None)
    if active_event:
        return jsonify({
            "active": True,
            "event": active_event,
            "remaining": int(event_data["end_time"] - now)
        })
    
    return jsonify({"active": False})
