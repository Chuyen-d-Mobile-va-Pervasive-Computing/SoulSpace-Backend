from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
from app.utils.pyobjectid import PyObjectId

class Reminder(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    title: str = Field(..., max_length=30)
    message: str = Field(..., max_length=200)
    time_of_day: str  # "HH:mm"
    repeat_type: str  # "once", "daily", "custom"
    repeat_days: Optional[List[int]] = None  # 0-6, chỉ cho "custom"
    is_active: bool = True

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}