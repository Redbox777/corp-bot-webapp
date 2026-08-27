
# 2. Сохраняем изменения (Ctrl+O → Enter → Ctrl+X)

# 3. Отправляем на GitHub
cd ~/corp-bot-webapp
git add -A
git commit -m "Описание обновления"
git push origin main

# 4. Ждём 1-2 минуты → Render обновится автоматически0
from flask import Flask, jsonify, request, send_from_directory
import os

app = Flask(__name__)
players = {}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/player/<chat_id>', methods=['GET'])
def get_player(chat_id):
    if chat_id not in players:
        players[chat_id] = {"balance": 0, "level": 1, "clicks": 0}
    return jsonify(players[chat_id])

@app.route('/api/click/<chat_id>', methods=['POST'])
def click(chat_id):
    if chat_id not in players:
        players[chat_id] = {"balance": 0, "level": 1, "clicks": 0}
    players[chat_id]["clicks"] += 1
    players[chat_id]["balance"] += 10
    players[chat_id]["level"] = (players[chat_id]["clicks"] // 100) + 1
    return jsonify(players[chat_id])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
