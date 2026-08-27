import json
from datetime import datetime
from config import config
from database import update_player

def get_quests_data(player):
    """Получить и обновить данные квестов"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Парсим quests_data
    raw_q = player.get("quests_data")
    if isinstance(raw_q, str):
        q_data = json.loads(raw_q) if raw_q else {}
    elif isinstance(raw_q, dict):
        q_data = raw_q
    else:
        q_data = {}
    
    # Обновляем прогресс
    for q in config.QUESTS:
        qid = q["id"]
        if qid not in q_data:
            q_data[qid] = {"progress": 0, "claimed": False, "last_date": today}
        
        # Сброс ежедневных квестов
        if q["daily"] and q_data[qid]["last_date"] != today:
            q_data[qid] = {"progress": 0, "claimed": False, "last_date": today}
        
        # Расчет прогресса
        val = 0
        t = q["type"]
        if t == "clicks":
            val = player.get("clicks", 0)
        elif t == "total_earned":
            val = player.get("total_earned", 0)
        elif t == "upgrades_count":
            val = sum((player.get("upgrades") or {}).values())
        elif t == "level":
            val = player.get("level", 1)
        elif t == "prestiges":
            val = player.get("total_prestiges", 0)
        
        q_data[qid]["progress"] = min(val, q["target"])
    
    return q_data

def save_quests_data(chat_id, q_data):
    """Сохранить данные квестов"""
    update_player(chat_id, quests_data=json.dumps(q_data))

def claim_quest(player, quest_id):
    """Получить награду за квест"""
    q_data = get_quests_data(player)
    
    if quest_id not in q_data or q_data[quest_id]["claimed"]:
        return None, "Already claimed"
    
    quest_def = next((q for q in config.QUESTS if q["id"] == quest_id), None)
    if not quest_def or q_data[quest_id]["progress"] < quest_def["target"]:
        return None, "Not ready"
    
    # Отмечаем как полученный
    q_data[quest_id]["claimed"] = True
    save_quests_data(player["chat_id"], q_data)
    
    return {"reward": quest_def["reward"]}, None
