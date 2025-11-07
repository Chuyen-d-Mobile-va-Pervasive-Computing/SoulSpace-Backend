from pydantic import BaseModel, Field, validator
from bson import ObjectId
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class GameSession(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    game_type: str  # "choose" | "match" | "crossword"
    score: int = Field(..., ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("game_type")
    def validate_game_type(cls, v):
        allowed = ["choose", "match", "crossword"]
        if v not in allowed:
            raise ValueError(f"game_type must be one of {allowed}")
        return v

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
