from domain.entities.telegram import TelegramBindRequest, TelegramVerification, TelegramAudit
from typing import Optional, List

class ITelegramBindRepository:
    def create(self, bind: TelegramBindRequest) -> TelegramBindRequest:
        raise NotImplementedError

    def get_by_id(self, bind_id: int) -> Optional[TelegramBindRequest]:
        raise NotImplementedError

    def get_pending_by_user(self, user_id: int) -> List[TelegramBindRequest]:
        raise NotImplementedError

    def update(self, bind: TelegramBindRequest) -> TelegramBindRequest:
        raise NotImplementedError

class ITelegramVerificationRepository:
    def create(self, verif: TelegramVerification) -> TelegramVerification:
        raise NotImplementedError

    def get_by_token(self, token: str) -> Optional[TelegramVerification]:
        raise NotImplementedError

    def get_pending_by_user(self, user_id: int) -> List[TelegramVerification]:
        raise NotImplementedError

    def update(self, verif: TelegramVerification) -> TelegramVerification:
        raise NotImplementedError

class ITelegramAuditRepository:
    def create(self, audit: TelegramAudit) -> TelegramAudit:
        raise NotImplementedError
