from domain.entities.telegram import TelegramChatToken, TelegramVerification, TelegramAudit
from typing import Optional, List

class ITelegramChatTokenRepository:
    def create(self, token: TelegramChatToken) -> TelegramChatToken:
        raise NotImplementedError
    
    def get_by_token(self, token_str: str) -> Optional[TelegramChatToken]:
        raise NotImplementedError
    
    def get_by_chat_id(self, chat_id: str) -> Optional[TelegramChatToken]:
        raise NotImplementedError
    
    def bind_token_to_user(self, token_str: str, user_id: int) -> Optional[TelegramChatToken]:
        raise NotImplementedError
    
    def get_by_user_id(self, user_id: int) -> Optional[TelegramChatToken]:
        raise NotImplementedError
    
    def unbind_tokens_by_user(self, user_id: int) -> int:
        raise NotImplementedError
    
    def upsert_token_for_chat(self, chat_id: str, token_str: str, username: str | None) -> TelegramChatToken:
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
