from pydantic import BaseModel, Field
from typing import Optional, List
from app.utils.pyobjectid import PyObjectId

class UserTestOptionSchema(BaseModel):
    option_id: str
    option_text: str
    score: int
    option_order: int

class UserTestQuestionSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    question_text: str
    question_order: int
    options: List[UserTestOptionSchema]

class UserTestSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    test_code: str
    title: str
    description: str
    image_url: Optional[str] = None
    severe_threshold: int
    expert_recommendation: str
    num_questions: int

class TestQuestionResponseSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    test_id: PyObjectId
    question_text: str
    question_order: int
    options: List[UserTestOptionSchema]

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