"""
Фоновые задачи Celery
"""
from celery import current_app
from datetime import datetime
import time
import json

# === БАЗОВЫЕ ЗАДАЧИ ===

@current_app.task(bind=True, max_retries=3)
def send_notification_task(self, chat_id: str, message: str, notification_type: str = "info"):
    """
    Отправка уведомления (асинхронно)
    """
    try:
        print(f"📩 Sending notification to {chat_id}: {message}")
        
        # Симуляция отправки (в реальности — Telegram API)
        time.sleep(0.5)
        
        # Логирование
        notification = {
            "chat_id": chat_id,
            "message": message,
            "type": notification_type,
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }
        
        print(f"✅ Notification sent: {json.dumps(notification, indent=2)}")
        return notification
        
    except Exception as exc:
        # Retry logic
        raise self.retry(exc=exc, countdown=60)

@current_app.task
def process_batch_clicks(chat_id: str, clicks_count: int):
    """
    Обработка пакетных кликов (оптимизация)
    """
    print(f" Processing {clicks_count} clicks for {chat_id}")
    
    from app.database import get_db, Player
    
    conn = get_db()
    result = []
    
    for i in range(clicks_count):
        click_result = Player.process_click(conn, chat_id)
        result.append(click_result)
    
    conn.close()
    
    total_balance = sum(r.get("balance", 0) for r in result)
    
    return {
        "chat_id": chat_id,
        "total_clicks": clicks_count,
        "final_balance": total_balance,
        "processed_at": datetime.now().isoformat()
    }

@current_app.task
def cleanup_old_cache():
    """
    Очистка старого кэша (периодическая задача)
    """
    print("🧹 Cleaning up old cache...")
    
    from app.utils.cache import clear_all_cache
    
    clear_all_cache()
    
    return {
        "status": "success",
        "message": "Cache cleared",
        "cleaned_at": datetime.now().isoformat()
    }

@current_app.task
def calculate_daily_stats():
    """
    Расчёт дневной статистики (периодическая задача)
    """
    print(" Calculating daily stats...")
    
    # Здесь можно подключить базу данных
    stats = {
        "total_players": 0,
        "active_players": 0,
        "total_clicks": 0,
        "calculated_at": datetime.now().isoformat()
    }
    
    print(f"📈 Daily stats: {json.dumps(stats, indent=2)}")
    return stats

@current_app.task(bind=True)
def heavy_computation_task(self, data_size: int = 1000):
    """
    Пример тяжёлой вычислительной задачи
    """
    print(f"🔢 Starting heavy computation ({data_size} items)...")
    
    total = 0
    for i in range(data_size):
        if i % 100 == 0:
            # Обновление прогресса
            progress = (i / data_size) * 100
            print(f"⏳ Progress: {progress:.1f}%")
        
        total += i * i
        
        # Симуляция тяжёлой работы
        time.sleep(0.001)
    
    return {
        "result": total,
        "data_size": data_size,
        "completed_at": datetime.now().isoformat()
    }

# === PERIODIC TASKS (Beat) ===

# Расписание периодических задач
CELERY_BEAT_SCHEDULE = {
    "cleanup-cache-every-hour": {
        "task": "app.tasks.cleanup_old_cache",
        "schedule": 3600.0,  # Каждый час
    },
    "daily-stats-every-day": {
        "task": "app.tasks.calculate_daily_stats",
        "schedule": 86400.0,  # Каждый день
    },
}
