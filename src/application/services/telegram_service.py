import os
import json
import secrets
import html
import urllib.request
from typing import Optional
from datetime import datetime
from domain.entities.telegram import TelegramChatToken, TelegramAudit
from domain.entities.user import User

TOKEN_REGEX = r'^[A-Za-z0-9_-]{8,128}$'

class TelegramService:
    def __init__(self, user_repo, chat_token_repo, audit_repo, bot_token: Optional[str] = None):
        self.user_repo = user_repo
        self.chat_token_repo = chat_token_repo
        self.audit_repo = audit_repo
        self.bot_token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN')
        self.api_base = f'https://api.telegram.org/bot{self.bot_token}' if self.bot_token else None
    
    def _send_api(self, method: str, payload: dict) -> Optional[dict]:
        if not self.api_base:
            return None
        url = f'{self.api_base}/{method}'
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read()
                return json.loads(body.decode('utf-8'))
        except Exception as e:
            try:
                self.audit_repo.create(TelegramAudit(id=None, user_id=None, event_type='telegram_api_error', ip=None, ua=None, details=str(e)))
            except Exception:
                pass
            return None
    
    def send_message(self, chat_id: str, text: str, reply_markup: dict | None = None) -> bool:
        if not self.api_base:
            return False
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        resp = self._send_api('sendMessage', payload)
        return bool(resp and resp.get('ok'))
    
    def create_token_for_chat(self, chat_id: str, username: Optional[str] = None) -> TelegramChatToken:
        """
        Создаёт token для chat_id, сохраняет запись и отправляет сообщение в чат.
        Сообщение теперь HTML-разметку: <b>, <code>.
        """
        token = secrets.token_urlsafe(24)
        chat_token = self.chat_token_repo.upsert_token_for_chat(chat_id, token, username)
        
        # Экранируем содержимое, чтобы избежать проблем если в username/token будут спецсимволы
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
        except Exception:
            try:
                self.audit_repo.create(TelegramAudit(id=None, user_id=None, event_type='token_send_failed', ip=None, ua=None, details=json.dumps({'chat_id': chat_id})))
            except Exception:
                pass
        
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
        self.user_repo.update(user)
        try:
            self.audit_repo.create(TelegramAudit(id=None, user_id=user.id, event_type='bind_success', ip=None, ua=None, details=json.dumps({'chat_id': bound.chat_id, 'token': token_str})))
        except Exception:
            pass
        return True, f'Telegram успешно привязан как @{bound.username}' if bound.username else 'Telegram успешно привязан'