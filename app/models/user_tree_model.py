from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class TreeAction(BaseModel):
    tree_action_id: PyObjectId = Field(default_factory=PyObjectId)
    action_id: PyObjectId
    action_date: datetime = Field(default_factory=datetime.utcnow)
    note: Optional[str] = Field(None, max_length=500)

class UserTree(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    total_xp: int = Field(default=0)
    streak_days: int = Field(default=0)
    last_watered_at: Optional[datetime] = None
    actions: List[TreeAction] = Field(default_factory=list)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True