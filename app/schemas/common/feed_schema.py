from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class FeedItemResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    type: Literal["user_post", "expert_article"] # Để FE phân biệt kiểu hiển thị (bài thường vs bài PR)
    
    # Thông tin tác giả (đã chuẩn hóa)
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    author_role: Literal["user", "expert"] # Để hiện badge chuyên gia
    
    # Nội dung
    content: str
    title: Optional[str] = None # Chỉ bài Expert mới có
    image_url: Optional[str] = None
    hashtags: List[str] = []
    
    # Tương tác
    like_count: int = 0
    comment_count: int = 0
    is_liked: bool = False
    is_owner: bool = False
    
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str, datetime: lambda v: v.isoformat()}