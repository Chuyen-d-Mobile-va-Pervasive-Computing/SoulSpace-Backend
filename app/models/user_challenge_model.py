from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.utils.pyobjectid import PyObjectId
from typing import List, Optional

class EarnedBadge(BaseModel):
    badge_id: PyObjectId
    name: str
    earned_at: datetime

class UserChallenge(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    challenge_id: PyObjectId
    progress: int = 0
    earned_points: int = 0
    badges: List[EarnedBadge] = []
    last_action_at: Optional[datetime] = None
    share_count: int = 0
    like_count: int = 0

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
