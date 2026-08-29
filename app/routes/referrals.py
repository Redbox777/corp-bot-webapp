from flask import Blueprint, jsonify, request
from app.database import get_db
import time

referrals_bp = Blueprint('referrals', __name__)

@referrals_bp.route('/referral_link/<chat_id>', methods=['GET'])
def get_referral_link(chat_id):
    """Получить реферальную ссылку"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT referral_code FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"error": "Player not found"}), 404
    
    bot = request.args.get('bot', 'MagnatZeroBot')
    return jsonify({
        "link": f"https://t.me/{bot}?start=ref_{row['referral_code']}",
        "code": row["referral_code"]
    })

@referrals_bp.route('/bind_referral/<chat_id>/<ref_code>', methods=['POST'])
def bind_referral(chat_id, ref_code):
    """Привязать реферала"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT referred_by FROM players WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    
    if not row or row["referred_by"]:
        conn.close()
        return jsonify({"error": "Already bound"}), 400
    
    c.execute('SELECT chat_id FROM players WHERE referral_code = ?', (ref_code,))
    ref = c.fetchone()
    
    if not ref or ref["chat_id"] == chat_id:
        conn.close()
        return jsonify({"error": "Invalid code"}), 400
    
    c.execute('UPDATE players SET referred_by = ? WHERE chat_id = ?', (ref["chat_id"], chat_id))
    c.execute('UPDATE players SET balance = balance + 500 WHERE chat_id IN (?, ?)', (ref["chat_id"], chat_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "bonus": 500})
