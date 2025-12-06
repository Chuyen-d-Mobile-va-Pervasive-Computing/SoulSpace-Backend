from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId
from typing import Optional
from datetime import datetime

class ExpertArticleCreate(BaseModel):
    title: str = Field(..., min_length=5)
    content: str = Field(..., min_length=20)
    image_url: Optional[str] = None

class ExpertArticleResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    expert_id: PyObjectId
    title: str
    content: str
    image_url: Optional[str]
    status: str
    created_at: datetime
    approved_at: Optional[datetime]

    class Config:
        json_encoders = {ObjectId: str}
        validate_by_name = True
