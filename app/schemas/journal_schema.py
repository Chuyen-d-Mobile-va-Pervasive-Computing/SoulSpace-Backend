from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TagSchema(BaseModel):
    tag_id: str
    tag_name: str

# Schema request (client gửi lên)
class JournalCreate(BaseModel):
    emotion_label: str
    emotion_emoji: str
    text_content: str
    voice_note_path: Optional[str] = None
    tags: Optional[List[TagSchema]] = None  # Thay đổi thành Optional[List[TagSchema]]

# Schema response (server trả về)
class JournalResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    emotion_label: str
    emotion_emoji: str
    text_content: str
    voice_note_path: Optional[str] = None
    voice_text: Optional[str] = None
    sentiment_label: str
    sentiment_score: float
    tags: Optional[List[TagSchema]] = None 