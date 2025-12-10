from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from app.utils.pyobjectid import PyObjectId

class Payment(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    appointment_id: PyObjectId
    user_id: PyObjectId
    expert_profile_id: PyObjectId
    method: Literal["card", "cash"]
    amount: int
    status: Literal["pending", "paid", "failed", "refunded"] = "pending"
    transaction_code: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda v: v.isoformat()}
