from pydantic import BaseModel, Field
from typing import List
from app.utils.pyobjectid import PyObjectId

class UserTestOptionSchema(BaseModel):
    option_id: str
    option_text: str
    score: int
    option_order: int

class UserTestQuestionSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    question_text: str
    question_order: int
    options: List[UserTestOptionSchema]
