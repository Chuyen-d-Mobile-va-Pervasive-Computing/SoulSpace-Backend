from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class AnonCommentCreate(BaseModel):
    post_id: PyObjectId = Field(...)
    content: str = Field(..., min_length=1)
    is_preset: bool = False

class AnonCommentResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    post_id: PyObjectId
    content: str
    moderation_status: str
    is_preset: bool
    created_at: datetime
    detected_keywords: list[str] = []

    class Config:
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        validate_by_name = True