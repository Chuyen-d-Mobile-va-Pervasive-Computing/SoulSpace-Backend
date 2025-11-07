from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId

class MatchPair(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    word: str = Field(..., max_length=100)
    meaning: str = Field(..., max_length=200)
    order: int = Field(default=0)
    is_active: bool = True

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
