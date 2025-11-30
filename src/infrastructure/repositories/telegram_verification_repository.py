import logging
from datetime import datetime
from typing import Optional, List
from domain.entities.telegram import TelegramVerification
from domain.repositories.telegram_repository import ITelegramVerificationRepository
from infrastructure.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

class TelegramVerificationRepository(ITelegramVerificationRepository):
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def create(self, verif: TelegramVerification) -> TelegramVerification:
        query = """
        INSERT INTO telegram_verifications (user_id, token, type, status, ip, created_at, expires_at, attempts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        created_at = datetime.utcnow().isoformat()
        expires_at = verif.expires_at.isoformat() if verif.expires_at else None
        verif_id = self.db.execute_update(query, (verif.user_id, verif.token, verif.type, verif.status, verif.ip, created_at, expires_at, verif.attempts))
        verif.id = verif_id
        verif.created_at = created_at
        return verif
    
    def get_by_token(self, token: str) -> Optional[TelegramVerification]:
        rows = self.db.execute_query("SELECT * FROM telegram_verifications WHERE token = ?", (token,))
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
        rows = self.db.execute_query("SELECT * FROM telegram_verifications WHERE user_id = ? AND status = 'pending' ORDER BY created_at DESC", (user_id,))
        result = []
        for r in rows:
            result.append(TelegramVerification(
                id=r['id'],
                user_id=r['user_id'],
                token=r['token'],
                type=r['type'],
                status=r['status'],
                ip=r['ip'],
                created_at=r['created_at'],
                expires_at=r['expires_at'],
                attempts=r['attempts']
            ))
        return result
    
    def update(self, verif: TelegramVerification) -> TelegramVerification:
        query = "UPDATE telegram_verifications SET status = ?, attempts = ?, expires_at = ? WHERE id = ?"
        expires_at = verif.expires_at.isoformat() if isinstance(verif.expires_at, datetime) else verif.expires_at
        self.db.execute_update(query, (verif.status, verif.attempts, expires_at, verif.id))
        return verif
    
    def expire_old(self) -> int:
        self.db.execute_update("UPDATE telegram_verifications SET status = 'expired' WHERE status = 'pending' AND expires_at IS NOT NULL AND expires_at <= ?", (datetime.utcnow().isoformat(),))
        return 1
    
    def update_status_if_pending(self, token: str, new_status: str) -> bool:
        """
        Если verification с token имеет status='pending' и не просрочен -> устанавливаем new_status.
        Возвращает True если обновили, False если не (уже другой статус/истёк/не найден/невалидный expires_at).
        """
        rows = self.db.execute_query(
            "SELECT * FROM telegram_verifications WHERE token = ? AND status = 'pending' LIMIT 1",
            (token,)
        )
        if not rows:
            logger.debug("update_status_if_pending: token not found or not pending: %s", token)
            return False
        
        r = rows[0]
        verif_id = r['id']
        
        expires_at_raw = r['expires_at']  
        if expires_at_raw:
            try:
                expires_dt = datetime.fromisoformat(expires_at_raw)
            except Exception as e:
                # Некорректный формат — логируем и помечаем как expired
                logger.warning("Invalid expires_at for verification id=%s token=%s: %s — expiring record", verif_id, token, e)
                try:
                    self.db.execute_update("UPDATE telegram_verifications SET status = 'expired' WHERE id = ?", (verif_id,))
                except Exception:
                    logger.exception("Failed to set verification expired for id=%s", verif_id)
                return False
            
            # Если просрочено — пометить expired и вернуть False
            if expires_dt <= datetime.utcnow():
                logger.info("Verification id=%s token=%s is expired (expires_at=%s) — marking expired", verif_id, token, expires_at_raw)
                try:
                    self.db.execute_update("UPDATE telegram_verifications SET status = 'expired' WHERE id = ?", (verif_id,))
                except Exception:
                    logger.exception("Failed to set verification expired for id=%s", verif_id)
                return False
        
        try:
            self.db.execute_update(
                "UPDATE telegram_verifications SET status = ? WHERE id = ? AND status = 'pending'",
                (new_status, verif_id)
            )
            logger.info("Verification id=%s token=%s updated to %s", verif_id, token, new_status)
            return True
        except Exception as e:
            logger.exception("Failed to update verification id=%s token=%s to %s: %s", verif_id, token, new_status, e)
            return False
