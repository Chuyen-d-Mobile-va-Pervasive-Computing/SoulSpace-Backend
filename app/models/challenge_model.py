from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId
from typing import List, Optional

class ChallengeAction(BaseModel):
    action_type: str  # write_journal, share_post, receive_like, etc.
    points: int
    description: str

class Challenge(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: str
    points: int
    required_progress: int
    actions: List[ChallengeAction] = []

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
