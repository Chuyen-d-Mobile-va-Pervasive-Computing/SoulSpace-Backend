from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
from app.utils.pyobjectid import PyObjectId

class AnonPostCreate(BaseModel):
    """
    Schema để tạo bài viết mới.
    - is_anonymous=True: Đăng ẩn danh (mặc định)
    - is_anonymous=False: Đăng bằng tên tài khoản
    """
    content: str = Field(..., min_length=1, max_length=5000, description="Nội dung bài viết")
    is_anonymous: bool = Field(default=True, description="True=Ẩn danh, False=Hiển thị tên")
    hashtags: List[str] = Field(default=[], description="Danh sách hashtags")

class AnonPostResponse(BaseModel):
    """
    Schema response cho bài viết.
    - Nếu is_anonymous=True: author_name = "Ẩn danh"
    - Nếu is_anonymous=False: author_name = username của người đăng
    """
    id: PyObjectId = Field(alias="_id")
    user_id: Optional[str] = None
    content: str
    is_anonymous: bool = True
    author_name: str = "Ẩn danh"
    hashtags: List[str] = []
    created_at: Optional[datetime] = None
    moderation_status: str = "Pending"
    ai_scan_result: Optional[str] = None
    flagged_reason: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    detected_keywords: List[str] = []
    is_liked: bool = False
    is_owner: bool = False

    @field_validator('hashtags', mode='before')
    @classmethod
    def ensure_hashtags_list(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return []

    @field_validator('detected_keywords', mode='before')
    @classmethod
    def ensure_keywords_list(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return []

    class Config:
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat() if v else None}
        populate_by_name = True