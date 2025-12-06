from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List, Optional
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class Option(BaseModel):
    option_id: str = Field(...)
    option_text: str = Field(..., max_length=200)
    score: int
    option_order: int

class TestQuestion(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    test_id: PyObjectId
    question_text: str = Field(..., max_length=500)
    question_order: int
    options: List[Option]
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}