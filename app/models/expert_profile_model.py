from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
from app.utils.pyobjectid import PyObjectId

class ExpertProfile(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # Reference to User
    user_id: PyObjectId = Field(...)  # 1-to-1 relationship
    
    # Personal Information
    full_name: str  # Họ tên thật (CÓ THỂ TRÙNG - dùng email để unique)
    phone: str = Field(...)
    date_of_birth: str  # Format: "dd/mm/yyyy"
    bio: Optional[str] = None
    avatar_url: Optional[str] = None  # Cloudinary URL
    
    # Professional Information
    years_of_experience: int  # 1-50
    clinic_name: str
    clinic_address: str
    certificate_url: str  # Cloudinary URL (required)
    
    # Approval Workflow
    status: Literal["pending", "approved", "rejected"] = Field(
        "pending"
    )
    approval_date: Optional[datetime] = None
    approved_by: Optional[PyObjectId] = None  # Admin user_id
    rejection_reason: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            PyObjectId: str
        }
