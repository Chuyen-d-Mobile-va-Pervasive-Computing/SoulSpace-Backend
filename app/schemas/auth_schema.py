from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
import re

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

    @validator("password")
    def validate_password(cls, v):
        if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", v):
            raise ValueError("Password must be at least 8 characters with 1 uppercase and 1 number")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    email: EmailStr
    created_at: str
    total_points: int

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6)

    @validator("new_password")
    def validate_new_password(cls, v):
        if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", v):
            raise ValueError("New password must be at least 8 characters with 1 uppercase and 1 number")
        return v

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    @validator("new_password")
    def validate_new_password(cls, v):
        if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", v):
            raise ValueError("New password must be at least 8 characters with 1 uppercase and 1 number")
        return v

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Confirm password does not match new password")
        return v