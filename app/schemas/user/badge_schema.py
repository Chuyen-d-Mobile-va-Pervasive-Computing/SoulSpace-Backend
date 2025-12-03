from pydantic import BaseModel
from typing import List

class BadgeResponse(BaseModel):
    """Response cho badge"""
    id: str
    name: str
    description: str
    icon: str
    points_required: int
    order: int

class UserBadgeResponse(BaseModel):
    """Response cho badge của user"""
    badge_id: str
    name: str
    description: str
    icon: str
    points_required: int
    earned_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "badge_id": "66f100...",
                "name": "PathFinder",
                "description": "Earn 10 points",
                "icon": "pathfinder",
                "points_required": 10,
                "earned_at": "2025-09-22T04:45:20.011Z"
            }
        }

class AllBadgesResponse(BaseModel):
    """Response tất cả badges (earned + locked)"""
    earned_badges: List[UserBadgeResponse]
    locked_badges: List[BadgeResponse]
    total_earned: int
    total_badges: int
