# app/schemas/user/expert_schema.py
from pydantic import BaseModel
from typing import List
from app.utils.pyobjectid import PyObjectId


class ExpertListItem(BaseModel):
    _id: str
    full_name: str
    avatar_url: str
    years_of_experience: int
    total_patients: int
    consultation_price: int

    class Config:
        json_encoders = {PyObjectId: str}


class ExpertListResponse(BaseModel):
    data: List[ExpertListItem]


class ExpertDetailResponse(BaseModel):
    _id: str
    full_name: str
    avatar_url: str
    phone: str
    email: str  # Lấy từ User model
    bio: str
    years_of_experience: int
    total_patients: int
    clinic_name: str
    clinic_address: str
    consultation_price: int

    class Config:
        json_encoders = {PyObjectId: str}


class AvailableSlotResponse(BaseModel):
    schedule_id: str
    start_time: str
    end_time: str

    class Config:
        json_encoders = {PyObjectId: str}


class AvailableTimesResponse(BaseModel):
    date: str
    slots: List[AvailableSlotResponse]