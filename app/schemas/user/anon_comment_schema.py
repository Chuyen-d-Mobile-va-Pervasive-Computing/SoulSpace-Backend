# app/schemas/user/anon_comment_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class AnonCommentCreate(BaseModel):
    post_id: PyObjectId = Field(...)
    content: str = Field(..., min_length=1)
    is_preset: bool = False
    is_anonymous: bool = False

class AnonCommentResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    post_id: PyObjectId

    user_id: Optional[str] = None   
    username: str = "Anonymous"          
    avatar_url: Optional[str] = None 
    is_owner: bool = False        
    role: str = "user"         
    is_anonymous: bool = False
    content: str
    moderation_status: str
    is_preset: bool
    created_at: datetime
    detected_keywords: List[str] = []

    class Config:
        json_encoders = {PyObjectId: str, datetime: lambda v: v.isoformat()}
        populate_by_name = True