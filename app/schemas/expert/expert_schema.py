from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, Literal
import re
from datetime import datetime

class ExpertRegister(BaseModel):
    """Phase 1: Sign up"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&#])", v):
            raise ValueError(
                "Password must contain uppercase, lowercase, number and special character"
            )
        return v
    
    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class ExpertProfileCreate(BaseModel):
    """Phase 2: Complete profile"""
    user_id: str
    full_name: str = Field(..., min_length=3, max_length=50)
    phone: str = Field(...)
    date_of_birth: str = Field(..., pattern=r"^\d{2}/\d{2}/\d{4}$")
    years_of_experience: int = Field(..., ge=1, le=50)
    clinic_name: str = Field(..., min_length=3, max_length=100)
    clinic_address: str = Field(..., min_length=10, max_length=200)
    bio: Optional[str] = Field(None, max_length=200)
    avatar_url: Optional[str] = None
    certificate_url: str  # Required
    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        """Allow letters (including Vietnamese) and spaces"""
        v = v.strip()
        
        # Check only letters and spaces
        for char in v:
            if not (char.isalpha() or char.isspace()):
                raise ValueError("Full name must contain only letters and spaces")
        
        # Check at least one letter
        if not any(char.isalpha() for char in v):
            raise ValueError("Full name must contain at least one letter")
        
        return v
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        """Vietnam phone: 10 digits starting with 0"""
        v = v.replace(" ", "").replace("-", "")
        
        if not re.match(r"^0\d{9}$", v):
            raise ValueError("Phone must be 10 digits starting with 0 (e.g., 0901234567)")
        
        return v
    
    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, v):
        """Age must be >= 25 years"""
        try:
            dob = datetime.strptime(v, "%d/%m/%Y").date()
            today = datetime.now().date()
            
            if dob > today:
                raise ValueError("Date of birth cannot be in the future")
            
            age = (today - dob).days / 365.25
            if age < 25:
                raise ValueError(f"Expert must be at least 25 years old (currently {int(age)} years old)")
            
            if age > 120:
                raise ValueError("Invalid date of birth")
            
            return v
        except ValueError as e:
            raise ValueError(str(e))


class ExpertProfileResponse(BaseModel):
    """Response after profile completion"""
    profile_id: str
    user_id: str
    full_name: str
    phone: str
    years_of_experience: int
    status: Literal["pending", "approved", "rejected"]
    created_at: str


class FileUploadResponse(BaseModel):
    """Response from file upload"""
    url: str
    public_id: str
    format: str
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None
