from pydantic import BaseModel
from typing import List, Optional, Literal

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

class StatTrendItem(BaseModel):
    value: int
    previous_value: int
    percent_change: float
    trend: Literal["up", "down", "neutral"]  # Mũi tên xanh/đỏ

class DashboardOverviewResponse(BaseModel):
    total_users: StatTrendItem
    total_posts: StatTrendItem
    positive_posts: StatTrendItem # Bài viết tích cực (dựa trên AI Sentiment hoặc Approved)
    ai_flagged: StatTrendItem     # Bài bị AI gắn cờ (Toxic/Blocked)

# --- Emotion Distribution Schema ---
class EmotionStatItem(BaseModel):
    label: str  # Positive, Negative, Neutral
    count: int
    percentage: float

# --- Chart Schema ---
class ChartDataPoint(BaseModel):
    label: str  # Trục X: Giờ (00:00), Ngày (2025-12-15), hoặc Tháng (Jan)
    value: int  # Trục Y: Số lượng

class DashboardChartResponse(BaseModel):
    period_type: str
    data: List[ChartDataPoint]