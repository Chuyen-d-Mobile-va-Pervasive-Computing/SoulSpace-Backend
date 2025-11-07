from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import Optional
from app.utils.pyobjectid import PyObjectId

class Badge(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., max_length=50)
    description: str = Field(..., max_length=200)
    icon: str = Field(..., max_length=50)
    points_required: int = Field(..., ge=0)
    challenge_id: Optional[PyObjectId] = None
    order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
