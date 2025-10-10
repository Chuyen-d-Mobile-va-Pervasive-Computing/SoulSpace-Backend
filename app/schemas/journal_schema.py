from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Schema request (client gửi lên)
class JournalCreate(BaseModel):
    emotion_label: str
    text_content: str
    voice_note_path: Optional[str] = None
    tags: Optional[List[str]] = None

# Schema response (server trả về)
class JournalResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    emotion_label: str
    text_content: str
    voice_note_path: Optional[str] = None
    voice_text: Optional[str] = None
    sentiment_label: str
    sentiment_score: float
    tags: Optional[List[str]] = None