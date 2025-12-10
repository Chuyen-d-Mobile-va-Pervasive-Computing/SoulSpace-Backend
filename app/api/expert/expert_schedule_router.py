from fastapi import APIRouter, Depends, Query
from app.schemas.expert.expert_schedule_schema import (
    ExpertScheduleCreate,
    ExpertScheduleResponse,
    ExpertScheduleListResponse
)
from app.services.expert.expert_schedule_service import ExpertScheduleService
from app.core.dependencies import get_current_expert, get_expert_schedule_service

router = APIRouter(prefix="/expert/schedules", tags=["Expert - Schedule"])

@router.post("/", response_model=ExpertScheduleResponse, status_code=201)
async def create_slot(
    payload: ExpertScheduleCreate,
    expert = Depends(get_current_expert),
    service: ExpertScheduleService = Depends(get_expert_schedule_service)
):
    return await service.create_schedule(str(expert["_id"]), payload)

@router.get("/", response_model=ExpertScheduleListResponse)
async def get_month_schedule(
    month: str = Query(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Tháng cần lấy lịch, định dạng YYYY-MM, ví dụ: 2025-12"
    ),
    expert = Depends(get_current_expert),
    service: ExpertScheduleService = Depends(get_expert_schedule_service)
):
    return await service.get_schedules_by_month(str(expert["_id"]), month)

@router.delete("/{schedule_id}")
async def delete_slot(
    schedule_id: str,
    expert = Depends(get_current_expert),
    service: ExpertScheduleService = Depends(get_expert_schedule_service)
):
    return await service.delete_schedule(schedule_id, str(expert["_id"]))
