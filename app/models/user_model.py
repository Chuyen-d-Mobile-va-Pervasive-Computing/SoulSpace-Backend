from pydantic import BaseModel, EmailStr, Field, model_validator
from bson import ObjectId
from datetime import datetime
from typing import Optional, Literal
from app.utils.pyobjectid import PyObjectId

class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    email: EmailStr
    password: str
    role: Literal["user", "admin", "expert"] = "user"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    total_points: int = 0
    reset_otp: Optional[str] = None
    reset_otp_expiry: Optional[datetime] = None
    is_active: bool = True
    
    # Expert-specific fields (Only when role="expert")
    expert_profile_id: Optional[PyObjectId] = None
    expert_status: Optional[Literal["pending", "approved", "rejected"]] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
    
    @model_validator(mode='after')
    def validate_expert_fields(self):
        """Validate expert fields consistency"""
        role = self.role
        expert_status = self.expert_status
        expert_profile_id = self.expert_profile_id
        
        if role == "expert":
            # Expert mới tạo phải có expert_status
            if not expert_status:
                self.expert_status = "pending"
        else:
            # Non-expert không được có expert fields
            if expert_status is not None or expert_profile_id is not None:
                raise ValueError(
                    "expert_status/expert_profile_id chỉ dùng cho role='expert'"
                )
        
        return self