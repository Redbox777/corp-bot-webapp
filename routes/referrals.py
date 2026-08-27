from flask import Blueprint, jsonify, request
from database import get_player, update_player, get_connection
from config import config
import time

referrals_bp = Blueprint('referrals', __name__)

@referrals_bp.route('/api/referral_link/<chat_id>', methods=['GET'])
def get_referral_link(chat_id):
    player = get_player(chat_id)
    if not player:
        return jsonify({"error": "Not found"}), 404
    
    bot = request.args.get('bot', config.BOT_USERNAME)
    ref_code = player["referral_code"]
    return jsonify({
        "link": f"https://t.me/{bot}?start=ref_{ref_code}",
        "code": ref_code
    })

@referrals_bp.route('/api/bind_referral/<chat_id>/<ref_code>', methods=['POST'])
def bind_referral(chat_id, ref_code):
    player = get_player(chat_id)
    if not player or player["referred_by"]:
        return jsonify({"error": "Already bound"}), 400
    
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT chat_id FROM players WHERE referral_code = ?', (ref_code,))
    referrer = c.fetchone()
    
    if not referrer or referrer["chat_id"] == chat_id:
        conn.close()
        return jsonify({"error": "Invalid code"}), 400
    
    ref_id = referrer["chat_id"]
    c.execute('UPDATE players SET referred_by = ? WHERE chat_id = ?', (ref_id, chat_id))
    c.execute('UPDATE players SET balance = balance + ? WHERE chat_id IN (?, ?)', 
              (config.REFERRAL_BONUS, ref_id, chat_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "bonus": config.REFERRAL_BONUS})
