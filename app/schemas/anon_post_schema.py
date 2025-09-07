from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId

class AnonPostCreate(BaseModel):
    content: str = Field(..., min_length=1)

class AnonPostResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    content: str
    moderation_status: str
    ai_scan_result: str | None
    flagged_reason: str | None
    like_count: int
    comment_count: int
    detected_keywords: list[str] = []

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True