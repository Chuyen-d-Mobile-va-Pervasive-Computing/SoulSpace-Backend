from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId

class Journal(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    emotion_label: Optional[str] = None
    text_content: Optional[str] = None
    voice_note_path: Optional[str] = None
    voice_text: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    tags: List[str] = []  # List of tag names
    # Toxic detection fields
    is_toxic: bool = False
    toxic_labels: List[str] = []
    toxic_confidence: float = 0.0

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}