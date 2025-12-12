# app/schemas/user/expert_schema.py
from pydantic import BaseModel, Field
from typing import List, Optional
from app.utils.pyobjectid import PyObjectId


class ExpertListItem(BaseModel):
    expert_profile_id: str = Field(..., alias="_id")
    full_name: str
    avatar_url: Optional[str]
    years_of_experience: int
    total_patients: int
    consultation_price: int

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str}


class ExpertListResponse(BaseModel):
    data: List[ExpertListItem]


class ExpertDetailResponse(BaseModel):
    expert_profile_id: str = Field(..., alias="_id")
    full_name: str
    avatar_url: Optional[str]
    phone: str
    email: Optional[str]
    bio: Optional[str]
    years_of_experience: int
    total_patients: int
    clinic_name: Optional[str]
    clinic_address: Optional[str]
    consultation_price: int

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str}


class AvailableSlotResponse(BaseModel):
    schedule_id: str
    start_time: str
    end_time: str

    class Config:
        json_encoders = {PyObjectId: str}


class AvailableTimesResponse(BaseModel):
    expert_profile_id: str
    date: str
    slots: List[AvailableSlotResponse]

    class Config:
        schema_extra = {
            "example": {
                "expert_profile_id": "671f3a9b2c1d4e5f6a7b8c90",
                "date": "2025-12-25",
                "slots": [
                    {
                        "schedule_id": "672a1b2c3d4e5f6a7b8c9012",
                        "start_time": "09:00",
                        "end_time": "10:00"
                    }
                ]
            }
        }