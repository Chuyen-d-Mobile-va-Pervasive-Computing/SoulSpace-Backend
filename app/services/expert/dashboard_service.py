# app/services/expert/dashboard_service.py
from fastapi import HTTPException, status
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.expert_repository import ExpertRepository
from app.repositories.expert_wallet_repository import ExpertWalletRepository
from app.repositories.user_repository import UserRepository
from app.schemas.expert.dashboard_schema import ExpertDashboardResponse, SummaryStats, ExpertInfo, AppointmentPreview, UserPreview
from datetime import datetime
import pytz
from typing import List

class ExpertDashboardService:
    def __init__(
        self,
        appointment_repo: AppointmentRepository,
        expert_repo: ExpertRepository,
        wallet_repo: ExpertWalletRepository,
        user_repo: UserRepository
    ):
        self.appointment_repo = appointment_repo
        self.expert_repo = expert_repo
        self.wallet_repo = wallet_repo
        self.user_repo = user_repo

    async def get_dashboard(self, expert_profile_id: str) -> ExpertDashboardResponse:
        # 1. Lấy thông tin chuyên gia
        expert = await self.expert_repo.get_by_id(expert_profile_id)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert profile not found")

        # 2. Lấy ví tiền
        wallet = await self.wallet_repo.get_by_expert_id(expert_profile_id)
        balance = wallet.balance if wallet else 0

        total_earned = wallet.total_earned if wallet else 0

        # 3. Đếm các loại lịch hẹn
        vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
        today_str = datetime.now(vn_tz).strftime("%Y-%m-%d")

        pending_appointments = await self.appointment_repo.get_by_expert_id(expert_profile_id, "pending")
        upcoming_appointments = await self.appointment_repo.get_by_expert_id(expert_profile_id, "upcoming")

        all_appointments = await self.appointment_repo.get_by_expert_id(expert_profile_id)
        appointments_today = len([
            apm for apm in all_appointments
            if apm.appointment_date == today_str
        ])

        # 4. Preview: lấy 2 pending + 2 upcoming gần nhất
        pending_preview = []
        for apm in sorted(pending_appointments, key=lambda x: (x.appointment_date, x.start_time))[:2]:
            user = await self.user_repo.get_by_id(str(apm.user_id))
            pending_preview.append(AppointmentPreview(
                _id=str(apm.id),
                appointment_date=apm.appointment_date,
                start_time=apm.start_time,
                user=UserPreview(
                    full_name=user.username if user else "Khách",
                    avatar_url=(user.avatar_url if user and user.avatar_url else "")
                ),
            ))

        upcoming_preview = []
        for apm in sorted(upcoming_appointments, key=lambda x: (x.appointment_date, x.start_time))[:2]:
            user = await self.user_repo.get_by_id(str(apm.user_id))
            upcoming_preview.append(AppointmentPreview(
                _id=str(apm.id),
                appointment_date=apm.appointment_date,
                start_time=apm.start_time,
                user=UserPreview(
                    full_name=user.username if user else "Khách",
                    avatar_url=(user.avatar_url if user and user.avatar_url else "")
                )
            ))

        return ExpertDashboardResponse(
            expert=ExpertInfo(
                full_name=expert.full_name,
                avatar_url=expert.avatar_url
            ),
            summary=SummaryStats(
                appointments_today=appointments_today,
                pending_count=len(pending_appointments),
                upcoming_count=len(upcoming_appointments),
                balance=balance
            ),
            pending_preview=pending_preview,
            upcoming_preview=upcoming_preview
        )