from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

class PartnerInfo(BaseModel):
    id: str  # user_id or expert_profile_id
    full_name: str
    avatar_url: Optional[str] = None
    online_status: bool = False
    last_seen_at: Optional[str] = None  # ISO string

class ChatSummaryResponse(BaseModel):
    chat_id: str
    partner: PartnerInfo
    last_message: str
    last_message_at: Optional[str] = None
    unread_count: int

class ChatListResponse(BaseModel):
    data: List[ChatSummaryResponse]

class MessageResponse(BaseModel):
    id: str
    sender_id: str
    sender_role: str
    content: str
    type: str = "text"
    file_url: Optional[str] = None
    created_at: str
    is_read: bool = False

class MessageListResponse(BaseModel):
    messages: List[MessageResponse]

class StartChatResponse(BaseModel):
    chat_id: str
    expert: PartnerInfo
    created: bool

# WebSocket schemas
class WebSocketMessage(BaseModel):
    event: Literal[
        "message.send",
        "typing.start",
        "typing.stop",
        "message.read",
        "ping",
        "presence.check" 
    ]
    payload: dict

class MessageSendPayload(BaseModel):
    message_type: Literal["text", "file"] = "text"
    content: str
    file_url: Optional[str] = None

class TypingPayload(BaseModel):
    is_typing: bool

class ReadReceiptPayload(BaseModel):
    message_id: str