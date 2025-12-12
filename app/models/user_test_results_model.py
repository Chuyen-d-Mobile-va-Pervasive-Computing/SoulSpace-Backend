# app/models/user_test_results_model.py
from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from app.utils.pyobjectid import PyObjectId
class SnapshotQuestion(BaseModel):
    question_id: PyObjectId
    question_text: str
    selected_option_id: str
    selected_option_text: str
    score: int
    
class TestSnapshot(BaseModel):
    test_title: str
    test_code: str
    questions: List[SnapshotQuestion]
    
class Answer(BaseModel):
    question_id: PyObjectId
    option_id: PyObjectId
    score_value: int
    
class UserTestResult(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    test_id: PyObjectId
    test_snapshot: Optional[TestSnapshot] = None # For completed
    status: str = Field(default="in-progress") # "in-progress" or "completed"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_score: Optional[int] = None
    result_level: Optional[str] = None
    feedback: Optional[str] = None
    answers: List[Answer] = [] # For in-progress
    created_at: Optional[datetime] = None
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}