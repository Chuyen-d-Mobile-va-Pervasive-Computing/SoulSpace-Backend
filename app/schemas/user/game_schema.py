from pydantic import BaseModel, Field, validator
from typing import List, Optional

# ===== REQUEST SCHEMAS =====

class GameCompleteRequest(BaseModel):
    """Request khi user hoàn thành minigame"""
    game_type: str  # "choose" | "match" | "crossword"
    score: int = Field(..., ge=0)

    @validator("game_type")
    def validate_game_type(cls, v):
        if v not in ["choose", "match", "crossword"]:
            raise ValueError("Invalid game_type")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "game_type": "choose",
                "score": 10
            }
        }

# ===== RESPONSE SCHEMAS =====

class BadgeInfo(BaseModel):
    """Badge info trong response"""
    id: str
    name: str
    description: str
    icon: str
    points_required: int

class GameCompleteResponse(BaseModel):
    """Response sau khi hoàn thành game"""
    earned_points: int
    total_points: int
    new_badges: List[BadgeInfo]
    message: str = "Game completed successfully"

    class Config:
        json_schema_extra = {
            "example": {
                "earned_points": 10,
                "total_points": 50,
                "new_badges": [
                    {
                        "id": "66f100...",
                        "name": "PathFinder",
                        "description": "Earn 10 points",
                        "icon": "pathfinder",
                        "points_required": 10
                    }
                ],
                "message": "Game completed successfully"
            }
        }

class QuestionResponse(BaseModel):
    """Response cho câu hỏi Choose game"""
    id: str
    question: str
    correct_answer: str
    options: List[str]
    meaning: str

class MatchPairResponse(BaseModel):
    """Response cho Match game"""
    id: str
    word: str
    meaning: str

class CrosswordWordResponse(BaseModel):
    """Response cho Crossword game"""
    id: str
    word: str
    clue: str

class UserPointsResponse(BaseModel):
    """Response cho tổng điểm user"""
    user_id: str
    total_points: int
    rank: Optional[int] = None  # Ranking trong leaderboard

class GameSessionResponse(BaseModel):
    """Response cho lịch sử chơi"""
    id: str
    game_type: str
    score: int
    created_at: str
