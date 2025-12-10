# app/api/expert/dashboard_router.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.expert.dashboard_schema import ExpertDashboardResponse
from app.services.expert.dashboard_service import ExpertDashboardService
from app.core.dependencies import get_current_expert, get_expert_dashboard_service

router = APIRouter(prefix="/expert/dashboard", tags=["Expert - Dashboard"])

@router.get("/", response_model=ExpertDashboardResponse)
async def get_dashboard(
    expert = Depends(get_current_expert),
    service: ExpertDashboardService = Depends(get_expert_dashboard_service)
):
    profile_id = expert.get("profile_id")
    if not profile_id:
        raise HTTPException(status_code=403, detail="Expert profile not found in token")
    return await service.get_dashboard(profile_id)