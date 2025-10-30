from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from app.utils.pyobjectid import PyObjectId

class Answer(BaseModel):
    question_id: PyObjectId
    option_id: PyObjectId
    score_value: int

class UserTestResult(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    test_id: PyObjectId
    test_code: str
    status: str = Field(default="in-progress") # "in-progress" hoặc "completed"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None # Chỉ có giá trị khi status là "completed"

    total_score: Optional[int] = None
    severity_level: Optional[str] = Field(None, max_length=50)
    result_label: Optional[str] = Field(None, max_length=100)
    guidance_notes: Optional[str] = Field(None, max_length=1000)
    needs_expert: Optional[bool] = None
    
    answers: List[Answer]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}