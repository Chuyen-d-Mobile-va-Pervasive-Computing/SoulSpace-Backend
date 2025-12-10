from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class Chat(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    expert_id: PyObjectId
    appointment_id: Optional[PyObjectId] = None
    last_message: str = ""
    last_message_at: Optional[datetime] = None
    user_unread: int = 0
    expert_unread: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda v: v.isoformat()}
