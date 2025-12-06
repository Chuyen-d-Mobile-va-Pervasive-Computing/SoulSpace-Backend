from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId
from typing import Literal

class Report(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    reporter_id: PyObjectId = Field(...)
    target_id: PyObjectId = Field(...)
    target_type: Literal["post", "comment"]
    reason: str
    status: Literal["pending", "resolved", "rejected"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
