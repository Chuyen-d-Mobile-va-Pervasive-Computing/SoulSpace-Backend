from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId

class AnonComment(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    post_id: PyObjectId = Field(...)
    user_id: PyObjectId = Field(...)
    content: str = Field(..., min_length=1)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    moderation_status: str = Field(default="Pending")  # Approved | Pending | Blocked
    is_preset: bool = False

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}