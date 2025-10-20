from pydantic import BaseModel, Field
from app.utils.pyobjectid import PyObjectId
from bson import ObjectId

class PositiveAction(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    action_name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}