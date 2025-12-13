from pydantic import BaseModel
from typing import List, Optional
from app.utils.pyobjectid import PyObjectId

class OptionCreateSchema(BaseModel):
    option_text: str
    score_value: int

class QuestionCreateSchema(BaseModel):
    question_text: str
    question_order: int
    options: List[OptionCreateSchema]

class TestUpdatePayloadSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severe_threshold: Optional[int] = None
    self_care_guidance: Optional[str] = None
    expert_recommendation: Optional[str] = None
    image_url: Optional[str] = None
    # If provided, this replaces ALL existing questions
    questions: Optional[List[QuestionCreateSchema]] = None


class TestCreateSchema(BaseModel):
    test_code: str
    title: str
    description: str
    severe_threshold: int
    expert_recommendation: str
    self_care_guidance: str
    image_url: Optional[str] = None
    questions: List[QuestionCreateSchema] # Bắt buộc phải có câu hỏi khi tạo mới