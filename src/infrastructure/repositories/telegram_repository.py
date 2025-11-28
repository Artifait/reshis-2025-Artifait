from datetime import datetime
from typing import List, Optional
from domain.entities.telegram import TelegramBindRequest, TelegramVerification, TelegramAudit
from domain.repositories.telegram_repository import ITelegramBindRepository, ITelegramVerificationRepository, ITelegramAuditRepository
from infrastructure.database.connection import DatabaseConnection

class TelegramBindRepository(ITelegramBindRepository):
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def create(self, bind: TelegramBindRequest) -> TelegramBindRequest:
        query = """
        INSERT INTO telegram_bind_requests (user_id, code, status, created_at, expires_at, attempts)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        created_at = datetime.utcnow()
        bind_id = self.db.execute_update(query, (bind.user_id, bind.code, bind.status, created_at, bind.expires_at, bind.attempts))
        bind.id = bind_id
        bind.created_at = created_at
        return bind

    def get_by_id(self, bind_id: int) -> Optional[TelegramBindRequest]:
        query = "SELECT * FROM telegram_bind_requests WHERE id = ?"
        rows = self.db.execute_query(query, (bind_id,))
        if not rows:
            return None
        row = rows[0]
        return TelegramBindRequest(
            id=row['id'],
            user_id=row['user_id'],
            code=row['code'],
            status=row['status'],
            created_at=row['created_at'],
            expires_at=row['expires_at'],
            attempts=row['attempts']
        )

    def get_pending_by_user(self, user_id: int) -> List[TelegramBindRequest]:
        query = "SELECT * FROM telegram_bind_requests WHERE user_id = ? AND status = 'pending' ORDER BY created_at DESC"
        rows = self.db.execute_query(query, (user_id,))
        return [
            TelegramBindRequest(
                id=r['id'],
                user_id=r['user_id'],
                code=r['code'],
                status=r['status'],
                created_at=r['created_at'],
                expires_at=r['expires_at'],
                attempts=r['attempts']
            ) for r in rows
        ]

    def update(self, bind: TelegramBindRequest) -> TelegramBindRequest:
        query = """
        UPDATE telegram_bind_requests
        SET code = ?, status = ?, expires_at = ?, attempts = ?
        WHERE id = ?
        """
        self.db.execute_update(query, (bind.code, bind.status, bind.expires_at, bind.attempts, bind.id))
        return bind


class TelegramVerificationRepository(ITelegramVerificationRepository):
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def create(self, verif: TelegramVerification) -> TelegramVerification:
        query = """
        INSERT INTO telegram_verifications (user_id, token, type, status, ip, created_at, expires_at, attempts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        created_at = datetime.utcnow()
        verif_id = self.db.execute_update(query, (verif.user_id, verif.token, verif.type, verif.status, verif.ip, created_at, verif.expires_at, verif.attempts))
        verif.id = verif_id
        verif.created_at = created_at
        return verif

    def get_by_token(self, token: str) -> Optional[TelegramVerification]:
        query = "SELECT * FROM telegram_verifications WHERE token = ?"
        rows = self.db.execute_query(query, (token,))
        if not rows:
            return None
        r = rows[0]
        return TelegramVerification(
            id=r['id'],
            user_id=r['user_id'],
            token=r['token'],
            type=r['type'],
            status=r['status'],
            ip=r['ip'],
            created_at=r['created_at'],
            expires_at=r['expires_at'],
            attempts=r['attempts']
        )

    def get_pending_by_user(self, user_id: int) -> List[TelegramVerification]:
        query = "SELECT * FROM telegram_verifications WHERE user_id = ? AND status = 'pending' ORDER BY created_at DESC"
        rows = self.db.execute_query(query, (user_id,))
        return [TelegramVerification(
            id=r['id'],
            user_id=r['user_id'],
            token=r['token'],
            type=r['type'],
            status=r['status'],
            ip=r['ip'],
            created_at=r['created_at'],
            expires_at=r['expires_at'],
            attempts=r['attempts']
        ) for r in rows]

    def update(self, verif: TelegramVerification) -> TelegramVerification:
        query = """
        UPDATE telegram_verifications
        SET status = ?, attempts = ?
        WHERE id = ?
        """
        self.db.execute_update(query, (verif.status, verif.attempts, verif.id))
        return verif


class TelegramAuditRepository(ITelegramAuditRepository):
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def create(self, audit: TelegramAudit) -> TelegramAudit:
        query = """
        INSERT INTO telegram_audit (user_id, event_type, ip, ua, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        created_at = datetime.utcnow()
        audit_id = self.db.execute_update(query, (audit.user_id, audit.event_type, audit.ip, audit.ua, audit.details, created_at))
        audit.id = audit_id
        audit.created_at = created_at
        return audit
