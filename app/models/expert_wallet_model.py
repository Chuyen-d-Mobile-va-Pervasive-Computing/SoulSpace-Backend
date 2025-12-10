from pydantic import BaseModel, Field
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class ExpertWallet(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    expert_profile_id: PyObjectId 
    balance: int = 0
    total_earned: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda v: v.isoformat()}
