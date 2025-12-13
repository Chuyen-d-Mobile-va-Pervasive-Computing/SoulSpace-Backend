from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class OptionResponseSchema(BaseModel):
    option_id: PyObjectId = Field(alias="_id") 
    option_text: str
    score_value: int

    class Config:
        from_attributes = True
        populate_by_name = True 
        json_encoders = {PyObjectId: str}

class TestQuestionResponseSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    test_id: PyObjectId
    question_text: str
    question_order: int
    options: List[OptionResponseSchema]

    class Config:
        from_attributes = True
        validate_by_name = True
        json_encoders = {PyObjectId: str}

class TestResponseSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    test_code: str
    title: str
    description: str
    num_questions: int
    severe_threshold: int
    self_care_guidance: Optional[str] = None
    expert_recommendation: str
    image_url: Optional[str] = None
    is_deleted: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        validate_by_name = True
        json_encoders = {PyObjectId: str}

class TestWithProgressResponseSchema(TestResponseSchema):
    completion_percentage: float = Field(..., description="Percentage 0-100")