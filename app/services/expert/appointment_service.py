# app/services/expert/appointment_service.py
from fastapi import HTTPException, status
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.expert_repository import ExpertRepository
from app.services.common.email_service import EmailService
from app.schemas.expert.appointment_schema import *
import logging

logger = logging.getLogger(__name__)

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
        """Get list of appointments for expert"""
        appointments = await self.appointment_repo.get_by_expert_id(expert_profile_id, status)
        data = []
        for apm in appointments:
            user = await self.user_repo.get_by_id(str(apm.user_id))
            if user:
                data.append({
                    "_id": str(apm.id),
                    "appointment_id": str(apm.id),
                    "date": apm.appointment_date,
                    "start_time": apm.start_time,
                    "user": {
                        "full_name": user.username or "Anonymous User",
                        "avatar_url": user.avatar_url or "",
                        "phone": user.phone
                    }
                })
        return ExpertAppointmentListResponse(data=data)

    async def get_detail(self, appointment_id: str, expert_profile_id: str):
        """Get detailed appointment information for expert"""
        appointment = await self.appointment_repo.get_by_id_for_expert(appointment_id, expert_profile_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        user = await self.user_repo.get_by_id(str(appointment.user_id))
        expert = await self.expert_repo.get_by_id(str(appointment.expert_profile_id))

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not expert:
            raise HTTPException(status_code=404, detail="Expert profile not found")

        return ExpertAppointmentDetailResponse(
            _id=str(appointment.id),
            user=UserInAppointment(
                full_name=user.username or "Anonymous User",
                avatar_url=user.avatar_url or "",
                phone=user.phone
            ),
            appointment_date=appointment.appointment_date,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            clinic={
                "name": expert.clinic_name or "Not specified",
                "address": expert.clinic_address or "Not specified"
            },
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
        """Accept or decline an appointment"""
        appointment = await self.appointment_repo.get_by_id_for_expert(appointment_id, expert_profile_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        payment = await self.payment_repo.get_latest_by_appointment(appointment_id)

        if action == "accept":
            if appointment.status != "pending":
                raise HTTPException(status_code=400, detail="Only pending appointments can be accepted")
            if not payment:
                raise HTTPException(status_code=400, detail="Payment information not found")
            if payment.method == "card" and payment.status != "paid":
                raise HTTPException(status_code=400, detail="Online payment must be completed before acceptance")
            if payment.method == "cash" and payment.status != "pending":
                raise HTTPException(status_code=400, detail="Cash payment status invalid for acceptance")

            # Accept transaction
            wallet = await self.appointment_repo.accept_appointment_transaction(appointment)

            # Send confirmation email to user
            try:
                user = await self.user_repo.get_by_id(str(appointment.user_id))
                expert = await self.expert_repo.get_by_id(str(appointment.expert_profile_id))
                if user and expert:
                    await self.email_service.send_appointment_accepted_email(
                        user_email=user.email,
                        expert_name=expert.full_name,
                        appointment_date=appointment.appointment_date,
                        start_time=appointment.start_time,
                        end_time=appointment.end_time,
                        clinic_name=expert.clinic_name or "Clinic",
                        clinic_address=expert.clinic_address or "Address not provided"
                    )
            except Exception as e:
                logger.warning(f"Failed to send acceptance email: {e}")

            updated_expert = await self.expert_repo.get_by_id(str(appointment.expert_profile_id))

            return ExpertAppointmentActionResponse(
                appointment_id=str(appointment.id),
                status="upcoming",
                wallet=WalletInfo(
                    balance=wallet.get("balance", 0),
                    total_earned=wallet.get("total_earned", 0)
                ),
                message=f"Appointment accepted successfully. Total patients: {updated_expert.total_patients if updated_expert else 'N/A'}"
            )

        elif action == "decline":
            await self.appointment_repo.decline_appointment_transaction(appointment, reason)

            # Handle payment refund/failure
            if payment:
                if payment.status == "paid":
                    await self.payment_repo.update_status(str(payment.id), "refunded")
                    try:
                        user = await self.user_repo.get_by_id(str(appointment.user_id))
                        if user:
                            await self.email_service.send_refund_email(
                                user_email=user.email,
                                amount=payment.amount,
                                appointment_date=appointment.appointment_date,
                                start_time=appointment.start_time
                            )
                    except Exception as e:
                        logger.warning(f"Failed to send refund email: {e}")
                elif payment.method == "cash" and payment.status == "pending":
                    await self.payment_repo.update_status(str(payment.id), "failed")

            # Notify user
            try:
                user = await self.user_repo.get_by_id(str(appointment.user_id))
                expert = await self.expert_repo.get_by_id(str(appointment.expert_profile_id))
                if user and expert:
                    await self.email_service.send_appointment_declined_email(
                        user_email=user.email,
                        expert_name=expert.full_name,
                        appointment_date=appointment.appointment_date,
                        start_time=appointment.start_time,
                        reason=reason or "No reason provided"
                    )
            except Exception as e:
                logger.warning(f"Failed to send decline email: {e}")

            return ExpertAppointmentActionResponse(
                appointment_id=str(appointment.id),
                status="cancelled",
                message="Appointment has been declined"
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Must be 'accept' or 'decline'")

    async def cancel_by_expert(self, appointment_id: str, expert_profile_id: str, reason: str):
        """Cancel appointment by expert"""
        if not reason or not reason.strip():
            raise HTTPException(status_code=400, detail="Cancel reason is required")

        appointment = await self.appointment_repo.get_by_id_for_expert(appointment_id, expert_profile_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if appointment.status not in ["pending", "upcoming"]:
            raise HTTPException(status_code=400, detail="Only pending or upcoming appointments can be cancelled")

        payment = await self.payment_repo.get_latest_by_appointment(appointment_id)

        await self.appointment_repo.cancel_by_expert_transaction(appointment, reason)

        # Handle refund for paid appointments
        if payment:
            if payment.method == "card" and payment.status == "paid":
                await self.payment_repo.update_status(str(payment.id), "refunded")
                try:
                    user = await self.user_repo.get_by_id(str(appointment.user_id))
                    if user:
                        await self.email_service.send_refund_email(
                            user_email=user.email,
                            amount=payment.amount,
                            appointment_date=appointment.appointment_date,
                            start_time=appointment.start_time
                        )
                except Exception as e:
                    logger.warning(f"Failed to send refund email: {e}")
            elif payment.method == "cash" and payment.status == "pending":
                await self.payment_repo.update_status(str(payment.id), "failed")

        # Notify user
        try:
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
        except Exception as e:
            logger.warning(f"Failed to send cancellation email: {e}")

        return ExpertAppointmentCancelResponse(
            message="Appointment cancelled successfully",
            appointment_id=appointment_id,
            status="cancelled"
        )