"""
Notifications Service - Уведомления
"""
from flask import Blueprint, jsonify, request
import time
from collections import deque

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notify')

# Notification storage
notifications_db = {}

@notifications_bp.route('/send/<chat_id>', methods=['POST'])
def send_notification(chat_id):
    """Отправить уведомление"""
    data = request.get_json() or {}
    
    notification = {
        "id": int(time.time() * 1000),
        "chat_id": chat_id,
        "message": data.get("message", "No message"),
        "type": data.get("type", "info"),
        "created_at": time.time(),
        "read": False
    }
    
    if chat_id not in notifications_db:
        notifications_db[chat_id] = deque(maxlen=100)
    
    notifications_db[chat_id].append(notification)
    
    return jsonify({
        "success": True,
        "notification": notification
    }), 201

@notifications_bp.route('/get/<chat_id>', methods=['GET'])
def get_notifications(chat_id):
    """Получить уведомления пользователя"""
    if chat_id not in notifications_db:
        return jsonify([])
    
    return jsonify(list(notifications_db[chat_id]))

@notifications_bp.route('/mark-read/<chat_id>/<int:notif_id>', methods=['POST'])
def mark_read(chat_id, notif_id):
    """Отметить уведомление как прочитанное"""
    if chat_id not in notifications_db:
        return jsonify({"error": "No notifications"}), 404
    
    for notif in notifications_db[chat_id]:
        if notif["id"] == notif_id:
            notif["read"] = True
            return jsonify({"success": True})
    
    return jsonify({"error": "Notification not found"}), 404

@notifications_bp.route('/stats', methods=['GET'])
def get_stats():
    """Статистика уведомлений"""
    total = sum(len(notifs) for notifs in notifications_db.values())
    read = sum(1 for notifs in notifications_db.values() for n in notifs if n.get("read"))
    
    return jsonify({
        "total_notifications": total,
        "read_notifications": read,
        "unread_notifications": total - read,
        "users_with_notifications": len(notifications_db)
    })
