from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId
from typing import List, Literal

class SensitiveKeyword(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    keyword: str
    category: str  # suicidal, violence, harassment, etc.
    severity: Literal["hard", "soft"]  # hard = block, soft = pending review
    variations: List[str] = []

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
