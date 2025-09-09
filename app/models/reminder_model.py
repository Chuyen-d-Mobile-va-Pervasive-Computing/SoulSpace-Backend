from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import Optional
from app.utils.pyobjectid import PyObjectId

class Reminder(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    title: str = Field(..., max_length=30)
    message: str = Field(..., max_length=200)
    remind_time: datetime
    is_active: bool = True
    is_custom: bool = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}