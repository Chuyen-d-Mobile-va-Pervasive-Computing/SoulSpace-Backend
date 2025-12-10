from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.schemas.user.expert_schema import (
    ExpertListResponse,
    ExpertDetailResponse,
    AvailableTimesResponse
)
from app.services.user.expert_service import UserExpertService
from app.core.dependencies import get_user_expert_service

router = APIRouter(prefix="/experts", tags=["User - Expert"])

@router.get("/", response_model=ExpertListResponse)
async def get_experts_list(service: UserExpertService = Depends(get_user_expert_service)):
    experts = await service.get_approved_experts()
    data = [
        {
            "_id": str(expert.id),
            "full_name": expert.full_name,
            "avatar_url": expert.avatar_url,
            "years_of_experience": expert.years_of_experience,
            "total_patients": expert.total_patients,
            "consultation_price": expert.consultation_price,
        }
        for expert in experts
    ]
    return ExpertListResponse(data=data)


@router.get("/{expert_profile_id}", response_model=ExpertDetailResponse)
async def get_expert_detail(
    expert_profile_id: str,
    service: UserExpertService = Depends(get_user_expert_service)
):
    expert = await service.get_expert_detail(expert_profile_id)
    return expert


@router.get("/{expert_profile_id}/available-times", response_model=AvailableTimesResponse)
async def get_available_times(
    expert_profile_id: str,
    date: str = Query(..., description="Required date in YYYY-MM-DD format"),
    service: UserExpertService = Depends(get_user_expert_service)
):
    slots_raw = await service.get_available_times(expert_profile_id, date)
    slots = [
        {
            "schedule_id": str(slot.id),
            "start_time": slot.start_time,
            "end_time": slot.end_time
        }
        for slot in slots_raw
    ]
    return AvailableTimesResponse(date=date, slots=slots)