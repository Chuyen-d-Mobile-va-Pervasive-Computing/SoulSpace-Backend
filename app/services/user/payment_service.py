# app/services/user/payment_service.py
from fastapi import HTTPException, status
from app.repositories.payment_repository import PaymentRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.expert_repository import ExpertRepository
from app.repositories.user_repository import UserRepository
from app.services.common.email_service import EmailService
from app.schemas.user.payment_schema import PaymentCreateResponse, PaymentBreakdown, AppointmentInfoInPayment, ExpertInfoInPayment
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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
        self.user_repo = UserRepository(expert_repo.db)  # Tái sử dụng db

    async def create_payment(self, user_id: str, appointment_id: str, method: str):
        if method not in ["card", "cash"]:
            raise HTTPException(status_code=400, detail="Invalid payment method")

        # Lấy thông tin appointment + validate
        appointment = await self.appointment_repo.get_by_id_for_user(appointment_id, user_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        if appointment.status != "pending":
            raise HTTPException(status_code=400, detail="Only pending appointments can be paid")

        # Kiểm tra đã thanh toán chưa
        existing = await self.payment_repo.get_latest_by_appointment(appointment_id)
        if existing and existing.status == "paid":
            raise HTTPException(status_code=400, detail="This appointment has already been paid")

        # Tạo payment
        payment_status = "paid" if method == "card" else "pending"
        payment = await self.payment_repo.create_payment(appointment, method, payment_status)

        # Lấy thông tin expert
        expert = await self.expert_repo.get_by_id(str(appointment.expert_profile_id))
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")

        expert_user = await self.user_repo.get_by_id(str(expert.user_id))
        expert_email = expert_user.email if expert_user else None

        # Gửi email thông báo cho chuyên gia (không làm fail API)
        try:
            if expert_email and hasattr(self.email_service, "send_payment_notification_to_expert"):
                await self.email_service.send_payment_notification_to_expert(
                    expert_email=expert_email,
                    expert_name=expert.full_name,
                    user_name="SoulSpace Customer",
                    appointment_date=appointment.appointment_date,
                    start_time=appointment.start_time,
                    clinic_name=expert.clinic_name or "Consultation Clinic",
                    clinic_address=expert.clinic_address or "Unknown address",
                    amount=f"{appointment.total_amount:,} VND",
                    method="Pay Online" if method == "card" else "Pay at Clinic"
                )
        except Exception as e:
            logger.warning(f"Failed to send payment email to expert: {e}")

        return PaymentCreateResponse(
            payment_id=str(payment.id),
            status=payment.status,
            method=method,
            amount=payment.amount,
            paid_at=payment.paid_at,
            appointment=AppointmentInfoInPayment(
                appointment_id=str(appointment.id),
                appointment_date=appointment.appointment_date,
                start_time=appointment.start_time,
                end_time=appointment.end_time
            ),
            expert=ExpertInfoInPayment(
                expert_profile_id=str(expert.id),
                full_name=expert.full_name,
                avatar_url=expert.avatar_url,
                clinic_name=expert.clinic_name,
                clinic_address=expert.clinic_address
            ),
            breakdown=PaymentBreakdown(
                price=appointment.price,
                vat=appointment.vat,
                after_hours_fee=getattr(appointment, "after_hours_fee", 0),
                discount=getattr(appointment, "discount", 0)
            )
        )