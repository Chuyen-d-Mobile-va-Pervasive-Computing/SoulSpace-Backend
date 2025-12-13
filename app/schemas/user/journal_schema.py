from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class JournalCreate(BaseModel):
    emotion_label: Optional[str] = None
    text_content: Optional[str]
    voice_note_path: Optional[str] = None
    tags: Optional[List[str]] = None

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
    is_toxic: bool = False
    toxic_labels: List[str] = []
    toxic_confidence: float = 0.0

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }