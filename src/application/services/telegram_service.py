import os
import json
import secrets
import html
import urllib.request
from typing import Optional, Tuple
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)

from domain.entities.telegram import TelegramChatToken, TelegramAudit, TelegramVerification
from domain.entities.user import User

TOKEN_REGEX = r'^[A-Za-z0-9_-]{8,128}$'

class TelegramService:
    def __init__(self, user_repo, chat_token_repo, audit_repo, chat_verification_repo=None, bot_token: Optional[str] = None):
        self.user_repo = user_repo
        self.chat_token_repo = chat_token_repo
        self.audit_repo = audit_repo
        self.chat_verification_repo = chat_verification_repo
        self.bot_token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured — TelegramService cannot operate")
        self.api_base = f'https://api.telegram.org/bot{self.bot_token}' if self.bot_token else None
    
    def _send_api(self, method: str, payload: dict) -> Optional[dict]:
        if not self.api_base:
            logger.warning("_send_api: api_base not configured, bot token missing. method=%s payload=%s", method, payload)
            return None
        url = f'{self.api_base}/{method}'
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read()
                text = body.decode('utf-8', errors='replace')
                return json.loads(text)
        except Exception as e:
            logger.exception("_send_api exception for url=%s: %s", url, e)
            # audit the failure if possible
            try:
                self.audit_repo.create(TelegramAudit(id=None, user_id=None, event_type='telegram_api_error', ip=None, ua=None, details=str(e)))
            except Exception:
                logger.exception("Failed to write audit for telegram_api_error")
            return None
    
    def send_message(self, chat_id: str, text: str, reply_markup: dict | None = None) -> bool:
        if not self.api_base:
            return False
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        resp = self._send_api('sendMessage', payload)
        return bool(resp and resp.get('ok'))
    
    def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False) -> bool:
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload['text'] = text
        if show_alert:
            payload['show_alert'] = True
        resp = self._send_api('answerCallbackQuery', payload)
        return bool(resp and resp.get('ok'))
    
    def create_token_for_chat(self, chat_id: str, username: Optional[str] = None) -> TelegramChatToken:
        token = secrets.token_urlsafe(24)
        chat_token = self.chat_token_repo.upsert_token_for_chat(chat_id, token, username)
        escaped_token = html.escape(token)
        escaped_botname = html.escape("CUDnevnik")
        text = (
            "🔐 Привязка <b>{}</b>\n\n"
            "Ваш токен для привязки:\n"
            "<code>{}</code>\n\n"
            "Скопируйте этот токен и вставьте в форму на сайте <b>\"Привязать Telegram\"</b>."
        ).format(escaped_botname, escaped_token)
        
        try:
            sent = self.send_message(chat_id, text)
            self.audit_repo.create(TelegramAudit(id=None, user_id=None, event_type='token_sent' if sent else 'token_send_failed', ip=None, ua=None, details=json.dumps({'chat_id': chat_id, 'token': token})))
        except Exception as e:
            logger.exception("create_token_for_chat exception")
            try:
                self.audit_repo.create(TelegramAudit(id=None, user_id=None, event_type='token_send_failed', ip=None, ua=None, details=json.dumps({'chat_id': chat_id, 'error': str(e)})))
            except Exception:
                logger.exception("Failed to write audit for token_send_failed")
        return chat_token
    
    def bind_user_with_token(self, user: User, token_str: str) -> tuple[bool, str]:
        import re
        if not token_str or not re.match(TOKEN_REGEX, token_str):
            return False, 'Неверный формат токена'
        token_row = self.chat_token_repo.get_by_token(token_str)
        if not token_row:
            return False, 'Токен не найден'
        if token_row.user_id is not None:
            return False, 'Токен уже использован'
        bound = self.chat_token_repo.bind_token_to_user(token_str, user.id)
        if not bound:
            return False, 'Не удалось привязать токен'
        # обновляем user
        user.telegram_id = bound.chat_id
        user.telegram_2fa_enabled = 1
        self.user_repo.update(user)
        try:
            self.audit_repo.create(TelegramAudit(id=None, user_id=user.id, event_type='bind_success', ip=None, ua=None, details=json.dumps({'chat_id': bound.chat_id, 'token': token_str})))
        except Exception:
            pass
        return True, f'Telegram успешно привязан как @{bound.username}' if bound.username else 'Telegram успешно привязан'
    
    def create_login_verification(self, user: User, ip: str, ttl_minutes: int = 5) -> TelegramVerification:
        # Сначала очищаем просроченные записи
        self.chat_verification_repo.expire_old()
        
        token = secrets.token_urlsafe(24)
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        verif = TelegramVerification(id=None, user_id=user.id, token=token, type='login', status='pending', ip=ip, created_at=None, expires_at=expires_at, attempts=0)
        verif = self.chat_verification_repo.create(verif)
        
        # Получаем chat для пользователя
        token_row = self.chat_token_repo.get_by_user_id(user.id)
        if not token_row:
            # нет привязки — логируем и возвращаем verif
            self.audit_repo.create(TelegramAudit(id=None, user_id=user.id, event_type='login_no_chat', ip=ip, ua=None, details=None))
            return verif
        
        chat_id = token_row.chat_id
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "Да", "callback_data": f"confirm_login:{token}"},
                    {"text": "Нет", "callback_data": f"deny_login:{token}"}
                ]
            ]
        }
        text = (
            f"⚠️ {html.escape(user.get_full_name())}, подтвердите авторизацию с устройства: {html.escape(str(ip))}\n\n"
            "❗️ Если это вы — нажмите \"Да\", иначе нажмите \"Нет\" и срочно смените пароль!"
        )
        sent_resp = self._send_api('sendMessage', {"chat_id": chat_id, "text": text, "reply_markup": reply_markup, "parse_mode": "HTML"})
        sent_ok = bool(sent_resp and sent_resp.get('ok'))
        self.audit_repo.create(TelegramAudit(id=None, user_id=user.id, event_type='login_request_sent' if sent_ok else 'login_request_failed', ip=ip, ua=None, details=json.dumps({'chat_id': chat_id, 'token': token})))
        return verif
    
    def handle_callback(self, callback_query: dict) -> tuple[bool, str]:
        cq_id = callback_query.get('id')
        data = (callback_query.get('data') or '').strip()
        from_user = callback_query.get('from') or {}
        chat_instance = callback_query.get('message', {}).get('chat', {}).get('id')
        
        # parse
        if ':' not in data:
            self.answer_callback_query(cq_id, "Неверная команда")
            return False, "bad format"
        action, token = data.split(':', 1)
        action = action.strip()
        token = token.strip()
        
        if action not in ('confirm_login', 'deny_login'):
            self.answer_callback_query(cq_id, "Неверная команда")
            return False, "unknown action"
        
        # попытаемся атомарно обновить статус (в репозитории проверяется expires_at)
        new_status = 'confirmed' if action == 'confirm_login' else 'denied'
        updated = self.chat_verification_repo.update_status_if_pending(token, new_status)
        if not updated:
            self.answer_callback_query(cq_id, "Срок действия истёк или запрос уже обработан")
            return False, "not pending/expired"
        
        # success
        if action == 'confirm_login':
            self.answer_callback_query(cq_id, "Вход подтверждён. Можно вернуться на сайт.")
            self.audit_repo.create(TelegramAudit(id=None, user_id=None, event_type='login_confirmed_by_user', ip=None, ua=None, details=json.dumps({'token': token, 'chat_id': chat_instance, 'from': from_user})))
            return True, "confirmed"
        else:
            self.answer_callback_query(cq_id, "Вход отклонён. Рекомендуем сменить пароль.")
            self.audit_repo.create(TelegramAudit(id=None, user_id=None, event_type='login_denied_by_user', ip=None, ua=None, details=json.dumps({'token': token, 'chat_id': chat_instance, 'from': from_user})))
            return True, "denied"