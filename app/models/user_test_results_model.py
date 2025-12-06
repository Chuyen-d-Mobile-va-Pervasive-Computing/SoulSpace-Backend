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

class UserTestResult(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    test_id: PyObjectId
    test_snapshot: TestSnapshot
    total_score: int
    result_level: str
    feedback: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}