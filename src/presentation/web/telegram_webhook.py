from flask import Blueprint, request, jsonify, current_app
import json
from application.services.telegram_service import TelegramService

bp = Blueprint('telegram_webhook', __name__)

@bp.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    app = current_app
    telegram_service: TelegramService = app.config.get('telegram_service')
    update = request.get_json(silent=True) or {}

    if not telegram_service:
        app.logger.error("Telegram service not configured")
        return jsonify({'ok': False, 'message': 'Telegram service not configured'}), 500

    callback_query = update.get('callback_query')
    if callback_query:
        try:
            ok, msg = telegram_service.handle_callback(callback_query)
            return jsonify({'ok': ok, 'message': msg})
        except Exception:
            app.logger.exception("Exception in handle_callback")
            try:
                cq_id = callback_query.get('id')
                telegram_service.answer_callback_query(cq_id, "Ошибка обработки (сервер). Попробуйте позже.")
            except Exception:
                app.logger.exception("Failed to answer callback_query after exception")
            return jsonify({'ok': False, 'message': 'internal error'}), 500

    message = update.get('message') or update.get('edited_message')
    if not message:
        app.logger.debug("No message in update")
        return jsonify({'ok': True})
    
    chat = message.get('chat', {})
    chat_id = str(chat.get('id'))
    username = chat.get('username') or chat.get('first_name') or None
    text = (message.get('text') or '').strip()
    if not text:
        app.logger.debug("Message text empty")
        return jsonify({'ok': True})

    if text.startswith('/start'):
        try:
            telegram_service.create_token_for_chat(chat_id, username)
        except Exception:
            app.logger.exception("Error in create_token_for_chat")
        return jsonify({'ok': True})

    app.logger.debug("Unhandled message: %s", text[:200])
    return jsonify({'ok': True})
