from flask import Flask, jsonify, request, send_from_directory
import os
import time

app = Flask(__name__)

# Хранилище игроков
players = {}

# Магазин улучшений
UPGRADES = {
    "shawarma": {"name": "Ларёк с шаурмой", "cost": 100, "income": 2, "icon": "🌯"},
    "coffee": {"name": "Кофейная точка", "cost": 500, "income": 10, "icon": "☕"},
    "office": {"name": "Офис", "cost": 2000, "income": 50, "icon": "🏢"},
    "factory": {"name": "Завод", "cost": 10000, "income": 250, "icon": "🏭"}
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/player/<chat_id>', methods=['GET'])
def get_player(chat_id):
    if chat_id not in players:
        players[chat_id] = {
            "balance": 0,
            "clicks": 0,
            "level": 1,
            "passive_income": 0,
            "upgrades": {},
            "last_update": time.time()
        }
    
    player = players[chat_id]
    
    # Начисляем пассивный доход за время оффлайн
    now = time.time()
    if player.get("last_update"):
        seconds_passed = now - player["last_update"]
        if seconds_passed > 1 and player.get("passive_income", 0) > 0:
            earned = int(player["passive_income"] * seconds_passed)
            player["balance"] += earned
    
    player["last_update"] = now
    return jsonify(player)

@app.route('/api/click/<chat_id>', methods=['POST'])
def click(chat_id):
    if chat_id not in players:
        players[chat_id] = {"balance": 0, "clicks": 0, "level": 1, "passive_income": 0, "upgrades": {}, "last_update": time.time()}
    
    players[chat_id]["clicks"] += 1
    players[chat_id]["balance"] += 10
    players[chat_id]["level"] = (players[chat_id]["clicks"] // 100) + 1
    players[chat_id]["last_update"] = time.time()
    
    return jsonify(players[chat_id])

@app.route('/api/shop', methods=['GET'])
def get_shop():
    return jsonify(UPGRADES)

@app.route('/api/buy/<chat_id>/<upgrade_id>', methods=['POST'])
def buy_upgrade(chat_id, upgrade_id):
    if chat_id not in players:
        return jsonify({"error": "Player not found"}), 404
    if upgrade_id not in UPGRADES:
        return jsonify({"error": "Invalid upgrade"}), 400
    
    player = players[chat_id]
    upgrade = UPGRADES[upgrade_id]
    
    # Динамическая цена: цена * (1.15 ^ количество)
    current_count = player.get("upgrades", {}).get(upgrade_id, 0)
    current_price = int(upgrade["cost"] * (1.15 ** current_count))
    
    if player["balance"] < current_price:
        return jsonify({"error": "Недостаточно монет"}), 400
    
    # Покупаем
    player["balance"] -= current_price
    if "upgrades" not in player:
        player["upgrades"] = {}
    player["upgrades"][upgrade_id] = current_count + 1
    player["passive_income"] = player.get("passive_income", 0) + upgrade["income"]
    player["last_update"] = time.time()
    
    # Новая цена для отображения
    next_price = int(upgrade["cost"] * (1.15 ** (current_count + 1)))
    
    return jsonify({
        "balance": player["balance"],
        "passive_income": player["passive_income"],
        "upgrades": player["upgrades"],
        "next_price": next_price,
        "success": True
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
