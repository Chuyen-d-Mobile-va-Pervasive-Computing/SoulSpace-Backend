# app/schemas/user/appointment_schema.py
from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class AppointmentCreateRequest(BaseModel):
    expert_profile_id: str
    schedule_id: str


class ExpertInAppointment(BaseModel):
    full_name: str
    avatar_url: Optional[str] = None
    clinic_name: Optional[str] = None


class AppointmentListItem(BaseModel):
    appointment_id: str = Field(..., alias="_id")
    date: str
    start_time: str
    status: Literal["pending", "upcoming", "past", "cancelled"]
    expert: ExpertInAppointment

    class Config:
        populate_by_name = True


class AppointmentListResponse(BaseModel):
    data: List[AppointmentListItem]


class AppointmentDetailResponse(BaseModel):
    appointment_id: str = Field(..., alias="_id")
    date: str
    start_time: str
    end_time: str
    status: Literal["pending", "upcoming", "past", "cancelled"]
    total_amount: int
    clinic_address: Optional[str] = None
    expert: ExpertInAppointment

   


class AppointmentCreateResponse(BaseModel):
    appointment_id: str = Field(..., alias="_id")
    status: str = "pending"
    appointment_date: str
    start_time: str
    end_time: str
    price: int
    vat: int
    total_amount: int

    class Config:
        populate_by_name = True


class AppointmentCancelRequest(BaseModel):
    cancel_reason: str = Field(..., min_length=1, description="Lý do hủy không được để trống")


class AppointmentCancelResponse(BaseModel):
    message: str
    appointment_id: str
    status: str = "cancelled"