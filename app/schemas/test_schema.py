from pydantic import BaseModel, Field
from typing import List, Optional
from app.utils.pyobjectid import PyObjectId

class OptionResponseSchema(BaseModel):
    option_id: PyObjectId 
    option_text: str
    score_value: int

    class Config:
        from_attributes = True
        validate_by_name = True
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
    test_name: str
    description: str
    num_questions: int
    severe_threshold: int
    self_care_guidance: str
    expert_recommendation: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True
        validate_by_name = True
        json_encoders = {PyObjectId: str}


class TestWithProgressResponseSchema(TestResponseSchema):
    completion_percentage: float = Field(..., description="Tỷ lệ phần trăm hoàn thành của bài test (0-100)")