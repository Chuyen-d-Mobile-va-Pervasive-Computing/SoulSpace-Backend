from pydantic import BaseModel
from typing import List, Optional

class UserPreview(BaseModel):
    full_name: str
    avatar_url: str

class AppointmentPreview(BaseModel):
    _id: str
    appointment_date: str
    start_time: str
    user: UserPreview

class SummaryStats(BaseModel):
    appointments_today: int
    pending_count: int
    upcoming_count: int
    balance: int

class ExpertInfo(BaseModel):
    full_name: str
    avatar_url: str

class ExpertDashboardResponse(BaseModel):
    expert: ExpertInfo
    summary: SummaryStats
    pending_preview: List[AppointmentPreview]
    upcoming_preview: List[AppointmentPreview]