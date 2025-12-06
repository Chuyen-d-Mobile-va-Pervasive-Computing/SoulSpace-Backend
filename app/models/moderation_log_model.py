from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId
from typing import List, Literal

class ModerationLog(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    content_id: PyObjectId
    content_type: Literal["post", "comment"]
    user_id: str
    text: str
    detected_keywords: List[str] = []
    action: Literal["Approved", "Pending", "Blocked", "Deleted"]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
