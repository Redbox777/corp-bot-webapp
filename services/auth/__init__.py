"""
Auth Service - Авторизация и пользователи
"""
from flask import Blueprint, jsonify, request
import time
import json

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# In-memory storage (в продакшене — база данных)
users_db = {}

@auth_bp.route('/register/<chat_id>', methods=['POST'])
def register(chat_id):
    """Регистрация нового пользователя"""
    if chat_id in users_db:
        return jsonify({"error": "User already exists"}), 400
    
    user_data = {
        "chat_id": chat_id,
        "created_at": time.time(),
        "last_login": time.time(),
        "is_active": True
    }
    users_db[chat_id] = user_data
    
    return jsonify({
        "success": True,
        "user": user_data,
        "message": "User registered"
    }), 201

@auth_bp.route('/login/<chat_id>', methods=['POST'])
def login(chat_id):
    """Вход пользователя"""
    if chat_id not in users_db:
        return jsonify({"error": "User not found"}), 404
    
    users_db[chat_id]["last_login"] = time.time()
    
    return jsonify({
        "success": True,
        "user": users_db[chat_id],
        "message": "Login successful"
    })

@auth_bp.route('/user/<chat_id>', methods=['GET'])
def get_user(chat_id):
    """Получить данные пользователя"""
    if chat_id not in users_db:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify(users_db[chat_id])

@auth_bp.route('/stats', methods=['GET'])
def get_stats():
    """Статистика сервиса авторизации"""
    return jsonify({
        "total_users": len(users_db),
        "active_users": sum(1 for u in users_db.values() if u.get("is_active"))
    })
