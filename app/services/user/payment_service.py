from fastapi import HTTPException, status
from app.repositories.payment_repository import PaymentRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.expert_repository import ExpertRepository
from app.services.common.email_service import EmailService
from app.schemas.user.payment_schema import PaymentCreateResponse, PaymentBreakdown

class UserPaymentService:
    def __init__(
        self,
        payment_repo: PaymentRepository,
        appointment_repo: AppointmentRepository,
        expert_repo: ExpertRepository,
        email_service: EmailService
    ):
        self.payment_repo = payment_repo
        self.appointment_repo = appointment_repo
        self.expert_repo = expert_repo
        self.email_service = email_service

    async def create_payment(self, user_id: str, appointment_id: str, method: str):
        if method not in ["card", "cash"]:
            raise HTTPException(status_code=400, detail="Invalid payment method")

        appointment = await self.appointment_repo.get_by_id_for_user(appointment_id, user_id)
        if not appointment or appointment.status != "pending":
            raise HTTPException(status_code=404, detail="Appointment not found or not pending")
        if appointment.status == "cancelled":
            raise HTTPException(status_code=400, detail="Appointment was cancelled, cannot pay")

        existing_payment = await self.payment_repo.get_latest_by_appointment(appointment_id)
        if existing_payment and existing_payment.status == "paid":
            raise HTTPException(status_code=400, detail="Payment already completed for this appointment")

        payment_status = "paid" if method == "card" else "pending"
        try:
            payment = await self.payment_repo.create_payment(appointment, method, payment_status)
        except Exception:
            raise HTTPException(status_code=500, detail="Payment failed, please try again")

        # Gửi email cho chuyên gia (không làm fail API nếu lỗi)
        try:
            expert = await self.expert_repo.get_by_id(str(appointment.expert_profile_id))
            expert_email = None
            if expert:
                # Lấy email từ user
                from app.repositories.user_repository import UserRepository
                user_repo = UserRepository(self.expert_repo.db)
                expert_user = await user_repo.get_by_id(str(expert.user_id))
                expert_email = expert_user.email if expert_user else None
            if expert and hasattr(self.email_service, "send_payment_notification_to_expert"):
                await self.email_service.send_payment_notification_to_expert(
                    expert_email=expert_email,
                    expert_name=expert.full_name,
                    user_name="Khách hàng SoulSpace",
                    appointment_date=appointment.appointment_date,
                    start_time=appointment.start_time,
                    clinic_name=expert.clinic_name,
                    clinic_address=expert.clinic_address,
                    amount=f"{appointment.total_amount:,} VND",
                    method="Thanh toán online (Thẻ)" if method == "card" else "Thanh toán tại phòng khám (Tiền mặt)"
                )
        except Exception as e:
            print(f"[WARNING] Send email failed: {e}")

        return PaymentCreateResponse(
            payment_id=str(payment.id),
            status=payment.status,
            amount=payment.amount,
            breakdown=PaymentBreakdown(
                price=appointment.price,
                vat=appointment.vat,
                after_hours_fee=getattr(appointment, "after_hours_fee", 0),
                discount=getattr(appointment, "discount", 0)
            )
        )
