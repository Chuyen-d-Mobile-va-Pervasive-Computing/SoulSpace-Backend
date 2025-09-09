from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.utils.pyobjectid import PyObjectId

class ReminderCreate(BaseModel):
    title: str = Field(..., max_length=30)
    message: str = Field(..., max_length=200)
    remind_time: datetime
    is_custom: bool = False

class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=30)
    message: Optional[str] = Field(None, max_length=200)
    remind_time: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_custom: Optional[bool] = None

class ReminderResponse(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    user_id: PyObjectId
    title: str
    message: str
    remind_time: str
    is_active: bool
    is_custom: bool

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
