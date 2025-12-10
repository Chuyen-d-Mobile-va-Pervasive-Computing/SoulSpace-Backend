from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
from app.utils.pyobjectid import PyObjectId

class ExpertProfile(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    full_name: str
    avatar_url: str
    phone: str
    bio: str
    years_of_experience: int
    clinic_name: str
    clinic_address: str
    consultation_price: int
    total_patients: int = 0
    status: Literal["pending", "approved", "rejected", "inactive"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # Legacy fields
    date_of_birth: Optional[str] = None
    certificate_url: Optional[str] = None
    approval_date: Optional[datetime] = None
    approved_by: Optional[PyObjectId] = None
    rejection_reason: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            PyObjectId: str
        }
