from fastapi import APIRouter, Depends
from app.schemas.user.payment_schema import PaymentCreateRequest, PaymentCreateResponse
from app.services.user.payment_service import UserPaymentService
from app.core.dependencies import get_current_user, get_user_payment_service

router = APIRouter(prefix="/payments", tags=["User - Payment"])

@router.post("/", response_model=PaymentCreateResponse, status_code=201)
async def create_payment(
    payload: PaymentCreateRequest,
    current_user = Depends(get_current_user),
    service: UserPaymentService = Depends(get_user_payment_service)
):
    return await service.create_payment(
        user_id=str(current_user["_id"]),
        appointment_id=payload.appointment_id,
        method=payload.method
    )
