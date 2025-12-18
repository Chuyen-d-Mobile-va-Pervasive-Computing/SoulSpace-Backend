from pydantic import BaseModel
from typing import List, Optional

class TopicStatItem(BaseModel):
    topic: str
    count: int


class UserActivityStat(BaseModel):
    user_id: str
    username: str
    avatar_url: Optional[str] = None
    count: int
    activity_type: str  