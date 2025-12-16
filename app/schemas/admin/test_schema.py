from pydantic import BaseModel, Field
from datetime import datetime
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
    questions: List[QuestionCreateSchema]
    
class AdminTestOptionSchema(BaseModel):
    option_id: str = Field(..., alias="_id")
    option_text: str
    score: int

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str}


class AdminTestQuestionSchema(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    test_id: PyObjectId
    question_text: str
    question_order: int
    options: List[AdminTestOptionSchema]

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str}


class AdminTestListSchema(BaseModel):
    id: PyObjectId = Field(..., alias="_id") 
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
        populate_by_name = True
        json_encoders = {PyObjectId: str}