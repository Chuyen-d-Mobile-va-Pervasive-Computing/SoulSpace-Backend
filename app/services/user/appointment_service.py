from fastapi import HTTPException, status
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.expert_repository import ExpertRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.services.common.email_service import EmailService
from app.schemas.user.appointment_schema import (
    AppointmentCreateResponse,
    AppointmentListResponse,
    AppointmentDetailResponse,
    AppointmentCancelResponse
)

class UserAppointmentService:
    def __init__(self, appointment_repo: AppointmentRepository, expert_repo: ExpertRepository, payment_repo: PaymentRepository, user_repo: UserRepository, email_service: EmailService):
        self.appointment_repo = appointment_repo
        self.expert_repo = expert_repo
        self.payment_repo = payment_repo
        self.user_repo = user_repo
        self.email_service = email_service

    async def create_appointment(self, user_id: str, expert_profile_id: str, schedule_id: str):
        expert = await self.expert_repo.get_by_id(expert_profile_id)
        if not expert or expert.status != "approved":
            raise HTTPException(status_code=404, detail="Expert not found or not approved")
        appointment, schedule = await self.appointment_repo.create_with_lock_slot(
            user_id, expert_profile_id, schedule_id, expert.consultation_price
        )
        return AppointmentCreateResponse(
            _id=str(appointment.id),
            appointment_date=appointment.appointment_date,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            price=appointment.price,
            vat=appointment.vat,
            total_amount=appointment.total_amount
        )

    async def get_appointment_list(self, user_id: str, status: str = None):
        appointments = await self.appointment_repo.get_list_by_user(user_id, status)
        data = []
        for apm in appointments:
            expert = await self.expert_repo.get_by_id(str(apm.expert_profile_id))
            if expert:
                data.append({
                    "_id": str(apm.id),
                    "date": apm.appointment_date,
                    "start_time": apm.start_time,
                    "status": apm.status,
                    "expert": {
                        "full_name": expert.full_name,
                        "avatar_url": expert.avatar_url,
                        "clinic_name": expert.clinic_name
                    }
                })
        return AppointmentListResponse(data=data)

    async def get_appointment_detail(self, appointment_id: str, user_id: str):
        appointment = await self.appointment_repo.get_by_id_for_user(appointment_id, user_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        expert = await self.expert_repo.get_by_id(str(appointment.expert_profile_id))
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")

        # Lấy user phone
        user = await self.user_repo.get_by_id(user_id)
        user_phone = user.phone if user else None

        # Lấy payment mới nhất
        payment = await self.payment_repo.get_latest_by_appointment(appointment_id)

        return AppointmentDetailResponse(
            _id=str(appointment.id),
            date=appointment.appointment_date,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            status=appointment.status,

            expert={
                "full_name": expert.full_name,
                "avatar_url": expert.avatar_url,
                "clinic_name": expert.clinic_name,
                "phone": expert.phone
            },

            user_phone=user_phone,

            pricing={
                "price": appointment.price,
                "vat": appointment.vat,
                "after_hours_fee": getattr(appointment, "after_hours_fee", 0),
                "discount": getattr(appointment, "discount", 0),
                "total_amount": appointment.total_amount
            },

            payment={
                "method": payment.method if payment else None
            }
        )

    async def cancel_appointment(self, appointment_id: str, user_id: str, cancel_reason: str):
        if not cancel_reason or not cancel_reason.strip():
            raise HTTPException(status_code=400, detail="Invalid cancel reason")
        
        appointment = await self.appointment_repo.get_by_id_for_user(appointment_id, user_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        if appointment.status != "pending":
            raise HTTPException(status_code=400, detail="Cannot cancel appointment that is already accepted or completed")
        
        payment = await self.payment_repo.get_latest_by_appointment(appointment_id)
        
        # Transaction cancel
        await self.appointment_repo.cancel_transaction(appointment, cancel_reason)
        
        if payment:
            if payment.method == "card" and payment.paid_at:
                await self.payment_repo.update_status(str(payment.id), "refunded")
                # Gửi email refund
                await self.email_service.send_refund_email(
                    user_email="user_email_from_db",  # Lấy từ user model nếu cần
                    amount=payment.amount,
                    appointment_date=appointment.appointment_date,
                    start_time=appointment.start_time
                )
            elif payment.method == "cash":
                await self.payment_repo.update_status(str(payment.id), "failed")
        
        return AppointmentCancelResponse(
            message="Hủy lịch hẹn thành công.",
            appointment_id=appointment_id,
            status="cancelled"
        )