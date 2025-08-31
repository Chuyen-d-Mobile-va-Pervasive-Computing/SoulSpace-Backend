from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId
from datetime import datetime
from typing import Optional
from app.utils.pyobjectid import PyObjectId

class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str = Field(..., max_length=50)
    email: EmailStr
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    total_points: int = 0

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}