from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Schema request (client gửi lên)
class JournalCreate(BaseModel):
    # FE hiện tại chưa gửi emotion_label ở bước /next => cho phép optional
    emotion_label: Optional[str] = None
    text_content: Optional[str]
    voice_note_path: Optional[str] = None
    # FE gửi tags dưới dạng JSON string của [{tag_id, tag_name}] => ta map thành List[str]
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
    # Toxic detection fields
    is_toxic: bool = False
    toxic_labels: List[str] = []
    toxic_confidence: float = 0.0