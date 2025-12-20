from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId

class Journal(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId
    created_at: datetime
    emotion_label: Optional[str] = None
    text_content: Optional[str] = None
    voice_note_path: Optional[str] = None
    voice_text: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    tags: List[str] = []
    is_toxic: bool = False
    toxic_labels: List[str] = []
    toxic_confidence: float = 0.0
    toxic_predictions: dict = {}

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        from_attributes=True
    )