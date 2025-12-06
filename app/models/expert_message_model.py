from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId
from typing import Optional, List, Literal

class ExpertMessage(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: Optional[PyObjectId] = None
    expert_id: Optional[PyObjectId] = None
    original_content: str
    detected_keywords: List[str] = []
    flagged_reason: str = ""
    ai_scan_result: str = "Unsafe"
    status: Literal["pending", "assigned", "in_progress", "resolved", "closed"] = "pending"
    expert_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
