from fastapi import HTTPException, status
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.expert_repository import ExpertRepository
from app.services.common.email_service import EmailService
from app.schemas.expert.appointment_schema import *

class ExpertAppointmentService:
    def __init__(
        self,
        appointment_repo: AppointmentRepository,
        payment_repo: PaymentRepository,
        user_repo: UserRepository,
        expert_repo: ExpertRepository,
        email_service: EmailService
    ):
        self.appointment_repo = appointment_repo
        self.payment_repo = payment_repo
        self.user_repo = user_repo
        self.expert_repo = expert_repo
        self.email_service = email_service

    async def get_list(self, expert_profile_id: str, status: str = None):
        appointments = await self.appointment_repo.get_by_expert_id(expert_profile_id, status)
        data = []
        for apm in appointments:
            user = await self.user_repo.get_by_id(str(apm.user_id))
            expert_profile = await self.expert_repo.get_by_id(str(apm.expert_profile_id))
            if user:
                data.append({
                    "_id": str(apm.id),
                    "appointment_id": str(apm.id),
                    "date": apm.appointment_date,
                    "start_time": apm.start_time,
                    "expert_profile_id": str(apm.expert_profile_id),
                    "user": {
                        "full_name": user.username or "User",
                        "avatar_url": user.avatar_url or "",
                        "phone": expert_profile.phone if expert_profile and getattr(expert_profile, "phone", None) is not None else None
                    }
                })
        return ExpertAppointmentListResponse(data=data)

    async def get_detail(self, appointment_id: str, expert_profile_id: str):
        appointment = await self.appointment_repo.get_by_id_for_expert(appointment_id, expert_profile_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found or not pending")

        user = await self.user_repo.get_by_id(str(appointment.user_id))
        expert = await self.expert_repo.get_by_id(str(appointment.expert_profile_id))
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if expert is None:
            raise HTTPException(status_code=404, detail="Expert not found")
        return ExpertAppointmentDetailResponse(
            _id=str(appointment.id),
            expert_profile_id=str(appointment.expert_profile_id), 
            user=UserInAppointment(
                full_name=user.username,
                avatar_url=user.avatar_url or "",
                phone=expert.phone if getattr(expert, "phone", None) is not None else ""
            ),
            appointment_date=appointment.appointment_date,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            clinic={"name": expert.clinic_name, "address": expert.clinic_address},
            pricing={
                "price": appointment.price,
                "vat": appointment.vat,
                "after_hours_fee": appointment.after_hours_fee,
                "discount": appointment.discount,
                "total_amount": appointment.total_amount
            },
            status=appointment.status,
            created_at=appointment.created_at.isoformat()
        )

    async def action(self, appointment_id: str, expert_profile_id: str, action: str, reason: str = None):
        appointment = await self.appointment_repo.get_by_id_for_expert(appointment_id, expert_profile_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found or not pending")

        payment = await self.payment_repo.get_latest_by_appointment(appointment_id)

        if action == "accept":
            if appointment.status != "pending":
                raise HTTPException(status_code=400, detail="Appointment must be pending to accept")
            if not payment:
                raise HTTPException(status_code=400, detail="Payment not found")
            if payment.method == "card" and payment.status != "paid":
                raise HTTPException(status_code=400, detail="Payment must be paid for online method")
            if payment.method == "cash" and payment.status != "pending":
                raise HTTPException(status_code=400, detail="Payment must be pending for cash method")

            # Transaction: update appointment, wallet, expert profile
            wallet = await self.appointment_repo.accept_appointment_transaction(appointment)
            expert_profile = await self.expert_repo.get_by_id(str(appointment.expert_profile_id))
            user = await self.user_repo.get_by_id(str(appointment.user_id))
            expert = expert_profile
            if user and expert:
                await self.email_service.send_appointment_accepted_email(
                    user_email=user.email,
                    expert_name=expert.full_name,
                    appointment_date=appointment.appointment_date,
                    start_time=appointment.start_time,
                    end_time=appointment.end_time,
                    clinic_name=expert.clinic_name,
                    clinic_address=expert.clinic_address
                )
            return ExpertAppointmentActionResponse(
                appointment_id=str(appointment.id),
                status="upcoming",
                wallet=WalletInfo(balance=wallet["balance"], total_earned=wallet["total_earned"]),
                message=f"Chấp nhận lịch hẹn thành công. Tổng số bệnh nhân: {expert_profile.total_patients}"
            )

        elif action == "decline":
            # Transaction: update appointment, free slot
            await self.appointment_repo.decline_appointment_transaction(appointment, reason)
            # Payment handling
            if payment:
                if payment.status == "paid":
                    await self.payment_repo.update_status(str(payment.id), "refunded")
                    user = await self.user_repo.get_by_id(str(appointment.user_id))
                    if user:
                        await self.email_service.send_refund_email(
                            user_email=user.email,
                            amount=payment.amount,
                            appointment_date=appointment.appointment_date,
                            start_time=appointment.start_time
                        )
                elif payment.method == "cash" and payment.status == "pending":
                    await self.payment_repo.update_status(str(payment.id), "failed")
            # Notify user
            user = await self.user_repo.get_by_id(str(appointment.user_id))
            expert = await self.expert_repo.get_by_id(str(appointment.expert_profile_id))
            if user and expert:
                await self.email_service.send_appointment_declined_email(
                    user_email=user.email,
                    expert_name=expert.full_name,
                    appointment_date=appointment.appointment_date,
                    start_time=appointment.start_time,
                    reason=reason
                )
            return ExpertAppointmentActionResponse(
                appointment_id=str(appointment.id),
                status="cancelled",
                message="Lịch hẹn đã bị từ chối bởi chuyên gia"
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    async def cancel_by_expert(self, appointment_id: str, expert_profile_id: str, reason: str):
        if not reason or not reason.strip():
            raise HTTPException(status_code=400, detail="Invalid cancel reason")

        appointment = await self.appointment_repo.get_by_id_for_expert(appointment_id, expert_profile_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if appointment.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel appointment that is already completed or cancelled."
            )

        # Lấy payment
        payment = await self.payment_repo.get_latest_by_appointment(appointment_id)

        # Transaction: hủy lịch + giải phóng slot
        await self.appointment_repo.cancel_by_expert_transaction(appointment, reason)

        # Xử lý hoàn tiền / failed
        if payment:
            if payment.method == "card" and payment.status == "paid":
                await self.payment_repo.update_status(str(payment.id), "refunded")
                # Gửi email hoàn tiền
                user = await self.user_repo.get_by_id(str(appointment.user_id))
                if user:
                    await self.email_service.send_refund_email(
                        user_email=user.email,
                        amount=payment.amount,
                        appointment_date=appointment.appointment_date,
                        start_time=appointment.start_time
                    )
            elif payment.method == "cash" and payment.status == "pending":
                await self.payment_repo.update_status(str(payment.id), "failed")

        # Gửi email thông báo hủy cho user
        user = await self.user_repo.get_by_id(str(appointment.user_id))
        expert = await self.expert_repo.get_by_id(str(appointment.expert_profile_id))
        if user and expert:
            await self.email_service.send_appointment_cancelled_by_expert_email(
                user_email=user.email,
                expert_name=expert.full_name,
                appointment_date=appointment.appointment_date,
                start_time=appointment.start_time,
                reason=reason
            )

        return ExpertAppointmentCancelResponse(
            message="Hủy lịch hẹn thành công.",
            appointment_id=appointment_id,
            status="cancelled"
        )