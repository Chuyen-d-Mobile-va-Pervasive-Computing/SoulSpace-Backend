from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId
from typing import Optional, List
from datetime import datetime

class ExpertArticleCreate(BaseModel):
    title: str = Field(..., min_length=5)
    content: str = Field(..., min_length=20)
    image_url: Optional[str] = None
    hashtags: List[str] = []

class ExpertArticleResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    expert_id: PyObjectId
    
    # Thông tin hiển thị tác giả (sẽ được enrich ở service/repo)
    expert_name: Optional[str] = None
    expert_avatar: Optional[str] = None
    
    title: str
    content: str
    image_url: Optional[str]
    hashtags: List[str] = []
    
    status: str
    created_at: datetime
    approved_at: Optional[datetime]
    
    # Thông tin tương tác
    like_count: int = 0
    comment_count: int = 0
    is_liked: bool = False # Check nếu user hiện tại đã like

    class Config:
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        populate_by_name = True