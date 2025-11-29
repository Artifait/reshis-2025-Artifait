from flask import Blueprint, request, jsonify, current_app
from application.services.telegram_service import TelegramService

bp = Blueprint('telegram_webhook', __name__)

@bp.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    app = current_app
    telegram_service: TelegramService = app.config.get('telegram_service')
    if not telegram_service:
        return jsonify({'ok': False, 'message': 'Telegram service not configured'}), 500
    
    update = request.get_json() or {}
    message = update.get('message') or update.get('edited_message')
    if not message:
        return jsonify({'ok': True})
    
    chat = message.get('chat', {})
    chat_id = str(chat.get('id'))
    username = chat.get('username') or chat.get('first_name') or None
    text = message.get('text', '')
    if not text:
        return jsonify({'ok': True})
    
    if text.strip().startswith('/start'):
        telegram_service.create_token_for_chat(chat_id, username)
    return jsonify({'ok': True})