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

class DailyPostCount(BaseModel):
    date: str  # Format: YYYY-MM-DD
    count: int

class PostStatsResponse(BaseModel):
    total_in_period: int
    daily_stats: List[DailyPostCount]