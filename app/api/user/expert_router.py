# app/api/user/expert_router.py
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
    """Lấy danh sách chuyên gia đã được duyệt"""
    experts = await service.get_approved_experts()
    data = [
        {
            "_id": str(expert.id),  # expert_profile_id
            "full_name": expert.full_name,
            "avatar_url": expert.avatar_url or "",
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
    """Lấy chi tiết chuyên gia theo expert_profile_id"""
    expert_data = await service.get_expert_detail(expert_profile_id)
    if not expert_data:
        raise HTTPException(status_code=404, detail="Expert not found")
    return expert_data  # Đã có expert_profile_id trong dict


@router.get("/{expert_profile_id}/available-times", response_model=AvailableTimesResponse)
async def get_available_times(
    expert_profile_id: str,
    date: str = Query(..., description="Date in YYYY-MM-DD format (e.g., 2025-12-25)"),
    service: UserExpertService = Depends(get_user_expert_service)
):
    """Lấy khung giờ trống của chuyên gia theo ngày"""
    try:
        slots_raw = await service.get_available_times(expert_profile_id, date)
        slots = [
            {
                "schedule_id": str(slot.id),
                "start_time": slot.start_time,
                "end_time": slot.end_time
            }
            for slot in slots_raw
        ]
        return AvailableTimesResponse(
            expert_profile_id=expert_profile_id, 
            date=date,
            slots=slots
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available times: {str(e)}"
        )