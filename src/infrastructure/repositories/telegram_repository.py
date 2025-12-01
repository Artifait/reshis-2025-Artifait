from datetime import datetime
from typing import Optional
from domain.entities.telegram import TelegramChatToken, TelegramAudit
from domain.repositories.telegram_repository import ITelegramChatTokenRepository, ITelegramAuditRepository
from infrastructure.database.connection import DatabaseConnection

class TelegramChatTokenRepository(ITelegramChatTokenRepository):
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def create(self, token: TelegramChatToken) -> TelegramChatToken:
        query = """
        INSERT INTO telegram_chat_tokens (chat_id, token, user_id, username, created_at, bound_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        created_at = datetime.utcnow().isoformat()
        token_id = self.db.execute_update(query, (token.chat_id, token.token, token.user_id, token.username, created_at, token.bound_at))
        token.id = token_id
        token.created_at = created_at
        return token

    def get_by_token(self, token_str: str) -> Optional[TelegramChatToken]:
        query = "SELECT * FROM telegram_chat_tokens WHERE token = ?"
        rows = self.db.execute_query(query, (token_str,))
        if not rows:
            return None
        r = rows[0]
        return TelegramChatToken(
            id=r['id'],
            chat_id=r['chat_id'],
            token=r['token'],
            user_id=r['user_id'],
            username=r['username'],
            created_at=r['created_at'],
            bound_at=r['bound_at']
        )

    def get_by_chat_id(self, chat_id: str) -> Optional[TelegramChatToken]:
        query = "SELECT * FROM telegram_chat_tokens WHERE chat_id = ? ORDER BY created_at DESC LIMIT 1"
        rows = self.db.execute_query(query, (chat_id,))
        if not rows:
            return None
        r = rows[0]
        return TelegramChatToken(
            id=r['id'],
            chat_id=r['chat_id'],
            token=r['token'],
            user_id=r['user_id'],
            username=r['username'],
            created_at=r['created_at'],
            bound_at=r['bound_at']
        )

    def get_by_user_id(self, user_id: int) -> Optional[TelegramChatToken]:
        query = "SELECT * FROM telegram_chat_tokens WHERE user_id = ? ORDER BY bound_at DESC LIMIT 1"
        rows = self.db.execute_query(query, (user_id,))
        if not rows:
            return None
        r = rows[0]
        return TelegramChatToken(
            id=r['id'],
            chat_id=r['chat_id'],
            token=r['token'],
            user_id=r['user_id'],
            username=r['username'],
            created_at=r['created_at'],
            bound_at=r['bound_at']
        )

    def bind_token_to_user(self, token_str: str, user_id: int) -> Optional[TelegramChatToken]:
        token_row = self.get_by_token(token_str)
        if not token_row:
            return None
        if token_row.user_id is not None:
            return None
        bound_at = datetime.utcnow().isoformat()
        query = "UPDATE telegram_chat_tokens SET user_id = ?, bound_at = ? WHERE id = ?"
        self.db.execute_update(query, (user_id, bound_at, token_row.id))
        token_row.user_id = user_id
        token_row.bound_at = bound_at
        return token_row

    def unbind_tokens_by_user(self, user_id: int) -> int:
        delete_query = "DELETE FROM telegram_chat_tokens WHERE user_id = ?"
        cur = self.db.execute_update(delete_query, (user_id,))
        return 1
    
    def upsert_token_for_chat(self, chat_id: str, token_str: str, username: str | None) -> TelegramChatToken:
        existing = self.get_by_chat_id(chat_id)
        now_iso = datetime.utcnow().isoformat()
        if existing:
            # обновляем запись
            # если запись ранее была привязана, сохраняем user_id и bound_at
            if existing.user_id:
                query = "UPDATE telegram_chat_tokens SET token = ?, username = ?, created_at = ? WHERE id = ?"
                self.db.execute_update(query, (token_str, username, now_iso, existing.id))
                existing.token = token_str
                existing.username = username
                existing.created_at = now_iso
                return existing
            else:
                # не привязана — обновляем token, username и обнуляем bound_at
                query = "UPDATE telegram_chat_tokens SET token = ?, username = ?, created_at = ?, bound_at = NULL WHERE id = ?"
                self.db.execute_update(query, (token_str, username, now_iso, existing.id))
                existing.token = token_str
                existing.username = username
                existing.created_at = now_iso
                existing.bound_at = None
                return existing
        else:
            # создаём новую запись
            new_token = TelegramChatToken(id=None, chat_id=chat_id, token=token_str, user_id=None, username=username, created_at=now_iso, bound_at=None)
            return self.create(new_token)

class TelegramAuditRepository(ITelegramAuditRepository):
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def create(self, audit: TelegramAudit) -> TelegramAudit:
        query = """
        INSERT INTO telegram_audit (user_id, event_type, ip, ua, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        created_at = datetime.utcnow().isoformat()
        audit_id = self.db.execute_update(query, (audit.user_id, audit.event_type, audit.ip, audit.ua, audit.details, created_at))
        audit.id = audit_id
        audit.created_at = created_at
        return audit

    def get_by_user_id(self, user_id: int) -> list:
        rows = self.db.execute_query("SELECT * FROM telegram_audit WHERE user_id = ? ORDER BY created_at DESC LIMIT 500", (user_id,))
        result = []
        for r in rows:
            result.append({
                'id': r['id'],
                'user_id': r['user_id'],
                'event_type': r['event_type'],
                'ip': r['ip'],
                'ua': r['ua'],
                'details': r['details'],
                'created_at': r['created_at']
            })
        return result

    def get_by_id(self, audit_id: int):
        rows = self.db.execute_query("SELECT * FROM telegram_audit WHERE id = ? LIMIT 1", (audit_id,))
        if not rows:
            return None
        r = rows[0]
        return {
            'id': r['id'],
            'user_id': r['user_id'],
            'event_type': r['event_type'],
            'ip': r['ip'],
            'ua': r['ua'],
            'details': r['details'],
            'created_at': r['created_at']
        }