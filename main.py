from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os

from config import config
from database import init_database
from routes.player import player_bp
from routes.shop import shop_bp
from routes.leaderboard import leaderboard_bp
from routes.referrals import referrals_bp

app = Flask(__name__)
CORS(app)

# Регистрируем blueprint'ы
app.register_blueprint(player_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(leaderboard_bp)
app.register_blueprint(referrals_bp)

# Главная страница
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Health check
@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# Импорт и регистрация rebirth и quests (требуют player)
@app.route('/api/rebirth/<chat_id>', methods=['POST'])
def rebirth_api(chat_id):
    from services.rebirth import do_rebirth
    from database import get_player
    player_row = get_player(chat_id)
    if not player_row:
        return jsonify({"error": "Player not found"}), 404
    player = dict(player_row)
    result, error = do_rebirth(player)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(result)

@app.route('/api/quests/<chat_id>', methods=['GET'])
def get_quests_api(chat_id):
    from services.quests import get_quests_data
    from database import get_player
    player_row = get_player(chat_id)
    if not player_row:
        return jsonify([])
    player = dict(player_row)
    q_data = get_quests_data(player)
    from config import config
    return jsonify([
        {**q, "progress": q_data.get(q["id"], {}).get("progress", 0), 
                "claimed": q_data.get(q["id"], {}).get("claimed", False)}
        for q in config.QUESTS
    ])

@app.route('/api/claim_quest/<chat_id>/<quest_id>', methods=['POST'])
def claim_quest_api(chat_id, quest_id):
    from services.quests import claim_quest
    from database import get_player, update_player
    player_row = get_player(chat_id)
    if not player_row:
        return jsonify({"error": "Not found"}), 404
    player = dict(player_row)
    result, error = claim_quest(player, quest_id)
    if error:
        return jsonify({"error": error}), 400
    update_player(chat_id, balance=player.get("balance", 0) + result["reward"])
    return jsonify({"success": True, "balance": player.get("balance", 0) + result["reward"], "reward": result["reward"]})

# Инициализация БД
init_database()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
