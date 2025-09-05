from pydantic import BaseModel
from typing import List
from datetime import datetime

class TagSchema(BaseModel):
    tag_id: str
    tag_name: str

# Schema request (client gửi lên)
class JournalCreate(BaseModel):
    emotion_label: str
    emotion_emoji: str
    text_content: str 
    tags: List[TagSchema] = []

# Schema response (server trả về)
class JournalResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    emotion_label: str
    emotion_emoji: str
    text_content: str
    sentiment_label: str
    sentiment_score: float
    tags: List[TagSchema] = []