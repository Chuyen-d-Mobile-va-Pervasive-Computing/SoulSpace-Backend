# app/schemas/user/payment_schema.py
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class PaymentCreateRequest(BaseModel):
    appointment_id: str
    method: Literal["card", "cash"]

class PaymentBreakdown(BaseModel):
    price: int = Field(...)
    vat: int = Field(...)
    after_hours_fee: int = Field(0)
    discount: int = Field(0)

class ExpertInfoInPayment(BaseModel):
    expert_profile_id: str = Field(...)
    full_name: str = Field(...)
    avatar_url: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None


class AppointmentInfoInPayment(BaseModel):
    appointment_id: str = Field(...)
    appointment_date: str = Field(...)
    start_time: str = Field(...)
    end_time: str = Field(...)

class PaymentCreateResponse(BaseModel):
    payment_id: str = Field(...)
    status: Literal["paid", "pending", "failed"]
    method: Literal["card", "cash"]
    amount: int = Field(...)
    paid_at: Optional[datetime] = None

    # Thông tin lịch hẹn
    appointment: AppointmentInfoInPayment

    # Thông tin chuyên gia
    expert: ExpertInfoInPayment

    # Chi tiết giá
    breakdown: PaymentBreakdown

    class Config:
        schema_extra = {
            "example": {
                "payment_id": "694a1b2c3d4e5f6a7b8c9012",
                "status": "paid",
                "method": "card",
                "amount": 550000,
                "paid_at": "2025-12-12T15:30:45.123Z",
                "appointment": {
                    "appointment_id": "693d1f2a3b4c5d6e7f8a9012",
                    "appointment_date": "2025-12-25",
                    "start_time": "09:00",
                    "end_time": "10:00"
                },
                "expert": {
                    "expert_profile_id": "671f3a9b2c1d4e5f6a7b8c90",
                    "full_name": "BS. Nguyễn Văn A",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "clinic_name": "SoulSpace Clinic",
                    "clinic_address": "123 Đường Láng, Hà Nội"
                },
                "breakdown": {
                    "price": 500000,
                    "vat": 50000,
                    "after_hours_fee": 0,
                    "discount": 0
                }
            }
        }