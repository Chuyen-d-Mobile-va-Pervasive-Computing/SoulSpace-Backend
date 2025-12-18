from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId
from typing import Literal, Optional, List

class ExpertArticle(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    expert_id: PyObjectId = Field(...)
    title: str
    content: str
    image_url: Optional[str] = None
    hashtags: List[str] = []  # Bổ sung hashtags
    
    status: Literal["pending", "approved", "rejected"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    
    # Bổ sung thông tin tương tác
    like_count: int = 0
    comment_count: int = 0

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}