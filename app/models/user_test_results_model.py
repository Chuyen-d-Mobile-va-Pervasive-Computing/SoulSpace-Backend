from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from app.utils.pyobjectid import PyObjectId

class Answer(BaseModel):
    question_id: PyObjectId
    option_id: PyObjectId
    score_value: int

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UserTestResult(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    test_id: PyObjectId
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    total_score: int
    severity_level: str = Field(..., max_length=50)
    result_label: str = Field(..., max_length=100)
    guidance_notes: str = Field(..., max_length=1000)
    needs_expert: bool
    answers: List[Answer]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}