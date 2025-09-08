from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId
from datetime import datetime

class AnonLike(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    post_id: PyObjectId
    user_id: PyObjectId
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        allow_population_by_field_name = True