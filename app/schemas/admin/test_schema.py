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

class AdminTestSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    test_code: str
    title: str
    description: str
    image_url: Optional[str] = None
    severe_threshold: int
    expert_recommendation: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[PyObjectId] = None
    updated_by: Optional[PyObjectId] = None
    is_deleted: bool = False
    questions: List[AdminTestQuestionSchema] = []
