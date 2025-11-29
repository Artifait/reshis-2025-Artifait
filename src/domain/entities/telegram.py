from dataclasses import dataclass
from datetime import datetime

@dataclass
class TelegramChatToken:
    id: int | None
    chat_id: str
    token: str
    user_id: int | None = None
    username: str | None = None
    created_at: datetime | None = None
    bound_at: datetime | None = None

@dataclass
class TelegramVerification:
    id: int | None
    user_id: int
    token: str
    type: str  # bind, login
    status: str  # pending, confirmed, denied, expired
    ip: str | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
    attempts: int = 0

@dataclass
class TelegramAudit:
    id: int | None
    user_id: int | None
    event_type: str | None
    ip: str | None
    ua: str | None
    details: str | None
    created_at: datetime | None = None
