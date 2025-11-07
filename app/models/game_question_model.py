from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List
from app.utils.pyobjectid import PyObjectId

class GameQuestion(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    question: str = Field(..., max_length=500)
    correct_answer: str = Field(..., max_length=200)
    options: List[str] = Field(..., min_length=2, max_length=6)
    meaning: str = Field(..., max_length=1000)
    order: int = Field(default=0)
    is_active: bool = True

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
