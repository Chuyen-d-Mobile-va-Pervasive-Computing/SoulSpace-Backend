from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List
from app.utils.pyobjectid import PyObjectId

class Option(BaseModel):
    option_id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    option_text: str = Field(..., max_length=200)
    score_value: int

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class TestQuestion(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    test_id: PyObjectId
    question_text: str = Field(..., max_length=500)
    question_order: int
    options: List[Option]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}