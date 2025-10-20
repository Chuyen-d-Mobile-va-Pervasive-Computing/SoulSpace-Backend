from pydantic import BaseModel, Field, constr
from typing import List, Optional
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class WaterTreePayloadSchema(BaseModel):
    action_id: PyObjectId
    positive_thoughts: List[constr(max_length=200)] = Field(..., min_length=1, max_length=3)

class PositiveActionResponseSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    action_name: str
    description: str

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {PyObjectId: str}

class UserTreeResponseSchema(BaseModel):
    
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    total_xp: int
    current_level_calculated: int
    current_xp_in_level: int
    xp_for_next_level: int
    streak_days: int
    last_watered_at: Optional[datetime]
    can_water_today: bool

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {PyObjectId: str}