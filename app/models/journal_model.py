from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId

class Tag(BaseModel):
    tag_id: str
    tag_name: str

class Journal(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)

    emotion_label: Optional[str] = None
    emotion_emoji: Optional[str] = None
    text_content: Optional[str] = None
    voice_note_path: Optional[str] = None
    voice_text: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    tags: List[dict] = []

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}