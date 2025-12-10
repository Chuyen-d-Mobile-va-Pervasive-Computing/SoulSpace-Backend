from pydantic import BaseModel
from typing import List, Literal, Optional

class AppointmentCreateRequest(BaseModel):
    expert_profile_id: str
    schedule_id: str

class ExpertInAppointment(BaseModel):
    full_name: str
    avatar_url: str
    clinic_name: Optional[str] = None

class AppointmentListItem(BaseModel):
    _id: str
    date: str
    start_time: str
    status: Literal["pending", "upcoming", "past", "cancelled"]
    expert: ExpertInAppointment

class AppointmentListResponse(BaseModel):
    data: List[AppointmentListItem]

class AppointmentDetailResponse(BaseModel):
    _id: str
    date: str
    start_time: str
    end_time: str
    status: Literal["pending", "upcoming", "past", "cancelled"]
    total_amount: int
    clinic_address: Optional[str] = None
    expert: ExpertInAppointment

class AppointmentCreateResponse(BaseModel):
    _id: str
    status: str = "pending"
    appointment_date: str
    start_time: str
    end_time: str
    price: int
    vat: int
    total_amount: int

class AppointmentCancelRequest(BaseModel):
    cancel_reason: str  # Bắt buộc, không rỗng

class AppointmentCancelResponse(BaseModel):
    message: str
    appointment_id: str
    status: str