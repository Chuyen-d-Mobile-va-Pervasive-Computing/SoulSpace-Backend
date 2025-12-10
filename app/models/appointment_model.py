from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from app.utils.pyobjectid import PyObjectId


class Appointment(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    expert_profile_id: PyObjectId
    schedule_id: PyObjectId
    appointment_date: str  # YYYY-MM-DD
    start_time: str
    end_time: str
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    price: int
    vat: int
    after_hours_fee: int = 0
    discount: int = 0
    total_amount: int
    status: Literal["pending", "upcoming", "past", "cancelled"] = "pending"
    cancel_reason: Optional[str] = None
    cancelled_by: Optional[Literal["user", "expert"]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda v: v.isoformat()}
