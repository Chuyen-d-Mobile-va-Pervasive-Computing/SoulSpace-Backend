from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class ChatMessage(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    chat_id: PyObjectId
    sender_role: Literal["user", "expert"]
    sender_id: PyObjectId
    type: Literal["text", "file"] = "text"
    content: str
    file_url: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda v: v.isoformat()}
