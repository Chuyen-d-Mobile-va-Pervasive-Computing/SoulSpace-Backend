from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from app.utils.pyobjectid import PyObjectId
from bson import ObjectId 

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
        orm_mode = True
        allow_population_by_field_name = True
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
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}