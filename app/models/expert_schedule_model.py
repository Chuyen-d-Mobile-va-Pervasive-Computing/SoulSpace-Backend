from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class ExpertSchedule(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    expert_id: PyObjectId
    date: str  # YYYY-MM-DD
    start_time: str  # HH:mm
    end_time: str  # HH:mm
    is_booked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda v: v.isoformat()}

