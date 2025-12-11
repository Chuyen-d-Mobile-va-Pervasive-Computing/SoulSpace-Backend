from pydantic import BaseModel
from typing import Literal, Optional, List

class UserInAppointment(BaseModel):
    full_name: str
    avatar_url: str
    phone: Optional[str] = None

class ExpertAppointmentListItem(BaseModel):
    _id: str
    appointment_id: str
    date: str
    start_time: str
    user: UserInAppointment

class ExpertAppointmentListResponse(BaseModel):
    data: List[ExpertAppointmentListItem]

class ExpertAppointmentDetailResponse(BaseModel):
    _id: str
    user: UserInAppointment
    appointment_date: str
    start_time: str
    end_time: str
    clinic: dict
    pricing: dict
    status: str
    created_at: str

class ExpertAppointmentActionRequest(BaseModel):
    action: Literal["accept", "decline"]
    reason: Optional[str] = None

class WalletInfo(BaseModel):
    balance: int
    total_earned: int

class ExpertAppointmentActionResponse(BaseModel):
    appointment_id: str
    status: str
    wallet: Optional[WalletInfo] = None
    message: str

class ExpertAppointmentCancelRequest(BaseModel):
    reason: str  # Bắt buộc

class ExpertAppointmentCancelResponse(BaseModel):
    message: str
    appointment_id: str
    status: str