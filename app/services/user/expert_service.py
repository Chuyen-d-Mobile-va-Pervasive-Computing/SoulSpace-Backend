from app.repositories.expert_repository import ExpertRepository
from app.repositories.expert_schedule_repository import ExpertScheduleRepository
from app.models.expert_profile_model import ExpertProfile
from app.models.expert_schedule_model import ExpertSchedule
from fastapi import HTTPException, status
from typing import List

class UserExpertService:
    def __init__(self, expert_repo: ExpertRepository, schedule_repo: ExpertScheduleRepository, user_repo=None):
        self.expert_repo = expert_repo
        self.schedule_repo = schedule_repo
        self.user_repo = user_repo

    async def get_approved_experts(self) -> List[ExpertProfile]:
        try:
            return await self.expert_repo.get_all(status="approved")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get approved experts: {str(e)}"
            )

    async def get_expert_detail(self, expert_profile_id: str):
        try:
            profile = await self.expert_repo.get_by_id(expert_profile_id)
            if not profile or profile.status != "approved":
                return None

            email = None
            if self.user_repo:
                user = await self.user_repo.get_by_id(str(profile.user_id))
                email = user.email if user else None

            return {
                "expert_profile_id": str(profile.id),
                "full_name": profile.full_name,
                "avatar_url": profile.avatar_url or "",
                "phone": profile.phone or "",
                "email": email,
                "bio": profile.bio or "",
                "years_of_experience": profile.years_of_experience,
                "total_patients": profile.total_patients,
                "clinic_name": profile.clinic_name or "",
                "clinic_address": profile.clinic_address or "",
                "consultation_price": profile.consultation_price,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get expert detail: {str(e)}"
            )

    async def get_available_times(self, expert_id: str, date: str) -> List[ExpertSchedule]:
        try:
            # Check if expert exists and approved
            await self.get_expert_detail(expert_id)
            return await self.schedule_repo.get_available_slots(expert_id, date)
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get available times: {str(e)}"
            )