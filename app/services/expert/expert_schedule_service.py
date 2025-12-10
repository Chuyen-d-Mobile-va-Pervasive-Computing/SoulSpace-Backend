from fastapi import HTTPException, status

from app.repositories.expert_schedule_repository import ExpertScheduleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.expert.expert_schedule_schema import (
    ExpertScheduleCreate,
    ExpertScheduleResponse,
    ExpertScheduleListResponse
)
from app.core.database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase


class ExpertScheduleService:
    def __init__(self, repo: ExpertScheduleRepository, db: AsyncIOMotorDatabase):
        self.repo = repo
        self.db = db

    async def _get_expert_profile_id(self, user_id: str) -> str:
        # Truy vấn expert_profile_id từ user_id
        user_repo = UserRepository(self.db)
        user = await user_repo.get_by_id(user_id)
        if not user or not user.expert_profile_id:
            raise HTTPException(status_code=403, detail="Expert profile not found")
        return str(user.expert_profile_id)

    async def create_schedule(self, user_id: str, data: ExpertScheduleCreate) -> ExpertScheduleResponse:
        expert_profile_id = await self._get_expert_profile_id(user_id)
        schedule = await self.repo.create_schedule(expert_profile_id, data.dict())
        return ExpertScheduleResponse(
            schedule_id=str(schedule.id),
            date=schedule.date,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            is_booked=schedule.is_booked
        )

    async def get_schedules_by_month(self, user_id: str, month: str) -> ExpertScheduleListResponse:
        expert_profile_id = await self._get_expert_profile_id(user_id)
        schedules = await self.repo.get_schedules_by_month(expert_profile_id, month)
        data = [
            ExpertScheduleResponse(
                schedule_id=str(s.id),
                date=s.date,
                start_time=s.start_time,
                end_time=s.end_time,
                is_booked=s.is_booked
            ) for s in schedules
        ]
        return ExpertScheduleListResponse(data=data)

    async def delete_schedule(self, schedule_id: str, user_id: str):
        expert_profile_id = await self._get_expert_profile_id(user_id)
        success = await self.repo.delete_schedule(schedule_id, expert_profile_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete schedule")
        return {"message": "Schedule deleted"}
