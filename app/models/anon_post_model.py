from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId

class AnonPost(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    content: str = Field(..., min_length=1)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    moderation_status: str = Field(default="Pending")  # Approved | Pending | Blocked
    ai_scan_result: str | None = None  # Safe | Suspicious | Unsafe
    flagged_reason: str | None = None

    like_count: int = 0
    comment_count: int = 0

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}