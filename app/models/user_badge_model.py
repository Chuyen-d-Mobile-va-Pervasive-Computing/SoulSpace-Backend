from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class UserBadge(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    badge_id: PyObjectId
    earned_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
