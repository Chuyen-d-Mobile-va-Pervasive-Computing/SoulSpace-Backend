from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.utils.pyobjectid import PyObjectId
from bson import ObjectId  # <--- Thêm dòng này

class SnapshotQuestionSchema(BaseModel):
    question_id: PyObjectId
    question_text: str
    selected_option_id: str
    selected_option_text: str
    score: int

class TestSnapshotSchema(BaseModel):
    test_title: str
    test_code: str
    questions: List[SnapshotQuestionSchema]

class UserTestResultSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    test_id: PyObjectId
    test_snapshot: TestSnapshotSchema
    total_score: int
    result_level: str
    feedback: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class SubmitAnswerSchema(BaseModel):
    question_id: PyObjectId
    chosen_option_id: PyObjectId

class SubmitTestPayloadSchema(BaseModel):
    answers: List[SubmitAnswerSchema] = Field(..., min_items=1)

class AnswerResponseSchema(BaseModel):
    question_id: PyObjectId
    option_id: PyObjectId
    score_value: int

    class Config:
        from_attributes = True
        validate_by_name = True
        json_encoders = {ObjectId: str}

class UserTestResultResponseSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    test_id: PyObjectId
    test_code: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    total_score: Optional[int] = None
    severity_level: Optional[str] = None
    result_label: Optional[str] = None
    guidance_notes: Optional[str] = None
    needs_expert: Optional[bool] = None
    
    answers: List[AnswerResponseSchema]

    class Config:
        from_attributes = True
        validate_by_name = True
        json_encoders = {ObjectId: str}


class CompletedTestSummarySchema(BaseModel):
    result_id: PyObjectId
    test_id: PyObjectId
    test_code: str
    test_name: str
    completed_at: datetime
    severity_level: str
    score_ratio: str = Field(..., description="Tỷ lệ điểm, ví dụ '6/27'")

    class Config:
        from_attributes = True
        validate_by_name = True
        json_encoders = {ObjectId: str}

class AnswerDetailSchema(BaseModel):
    question_text: str
    chosen_option_text: str
    score_value: int

class UserTestResultDetailSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    test_id: PyObjectId
    test_code: str
    test_name: str
    status: str
    completed_at: Optional[datetime]
    total_score: Optional[int]
    max_score: Optional[int]
    severity_level: Optional[str]
    result_label: Optional[str]
    guidance_notes: Optional[str]
    needs_expert: Optional[bool]
    answered_questions: List[AnswerDetailSchema]

    class Config:
        from_attributes = True
        validate_by_name = True
        json_encoders = {ObjectId: str}