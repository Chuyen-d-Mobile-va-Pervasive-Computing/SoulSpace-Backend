from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class AdminTestOptionSchema(BaseModel):
    option_id: str
    option_text: str
    score: int
    option_order: int

class AdminTestQuestionSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    test_id: PyObjectId
    question_text: str
    question_order: int
    options: List[AdminTestOptionSchema]
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
