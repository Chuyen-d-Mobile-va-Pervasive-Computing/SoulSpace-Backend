from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId
from typing import Literal, Optional
from datetime import datetime

class ReportCreate(BaseModel):
    target_id: str = Field(...)
    target_type: Literal["post", "comment"]
    reason: str = Field(..., min_length=1)

class ReportResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    reporter_id: Optional[PyObjectId] = None
    target_id: PyObjectId
    target_type: str
    reason: str
    status: str
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
        extra = "allow"
