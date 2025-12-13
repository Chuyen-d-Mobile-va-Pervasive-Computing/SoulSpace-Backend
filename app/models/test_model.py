from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class Test(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    test_code: str = Field(..., max_length=50)
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    num_questions: int = Field(default=0)
    image_url: Optional[str] = None
    severe_threshold: int
    self_care_guidance: str = Field(default="", max_length=1000)
    expert_recommendation: str = Field(..., max_length=1000)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[PyObjectId] = None
    updated_by: Optional[PyObjectId] = None
    is_deleted: bool = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}