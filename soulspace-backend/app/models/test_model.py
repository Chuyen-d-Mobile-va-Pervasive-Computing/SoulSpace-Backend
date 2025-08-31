from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional
from app.utils.pyobjectid import PyObjectId

class Test(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    test_code: str = Field(..., max_length=50)
    test_name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    num_questions: int
    severe_threshold: int
    self_care_guidance: str = Field(..., max_length=1000)
    expert_recommendation: str = Field(..., max_length=1000)
    image_url: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}