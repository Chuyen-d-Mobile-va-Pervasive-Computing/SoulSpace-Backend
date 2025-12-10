from pydantic import BaseModel
from typing import Literal

class PaymentCreateRequest(BaseModel):
    appointment_id: str
    method: Literal["card", "cash"]

class PaymentBreakdown(BaseModel):
    price: int
    vat: int
    after_hours_fee: int = 0
    discount: int = 0

class PaymentCreateResponse(BaseModel):
    payment_id: str
    status: Literal["paid", "pending", "failed"]
    amount: int
    breakdown: PaymentBreakdown
