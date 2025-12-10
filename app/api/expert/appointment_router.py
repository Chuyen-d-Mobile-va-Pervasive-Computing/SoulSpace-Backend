from fastapi import APIRouter, Depends, Query, HTTPException
from app.schemas.expert.appointment_schema import *
from app.services.expert.appointment_service import ExpertAppointmentService
from app.core.dependencies import get_current_expert, get_expert_appointment_service

router = APIRouter(prefix="/expert/appointments", tags=["Expert - Appointments"])

@router.get("/", response_model=ExpertAppointmentListResponse)
async def get_appointments(
    status: str = Query(None, regex="^(pending|upcoming|past|cancelled)$"),
    expert = Depends(get_current_expert),
    service: ExpertAppointmentService = Depends(get_expert_appointment_service)
):
    expert_profile_id = expert.get("profile_id")
    if not expert_profile_id:
        raise HTTPException(status_code=403, detail="Expert profile not found in token")
    return await service.get_list(expert_profile_id, status)

@router.get("/{appointment_id}", response_model=ExpertAppointmentDetailResponse)
async def get_detail(
    appointment_id: str,
    expert = Depends(get_current_expert),
    service: ExpertAppointmentService = Depends(get_expert_appointment_service)
):
    expert_profile_id = expert.get("profile_id")
    if not expert_profile_id:
        raise HTTPException(status_code=403, detail="Expert profile not found in token")
    return await service.get_detail(appointment_id, expert_profile_id)

@router.post("/{appointment_id}/action", response_model=ExpertAppointmentActionResponse)
async def action(
    appointment_id: str,
    payload: ExpertAppointmentActionRequest,
    expert = Depends(get_current_expert),
    service: ExpertAppointmentService = Depends(get_expert_appointment_service)
):
    expert_profile_id = expert.get("profile_id")
    if not expert_profile_id:
        raise HTTPException(status_code=403, detail="Expert profile not found in token")
    return await service.action(appointment_id, expert_profile_id, payload.action, payload.reason)

@router.delete("/{appointment_id}", response_model=ExpertAppointmentCancelResponse)
async def cancel_appointment_by_expert(
    appointment_id: str,
    payload: ExpertAppointmentCancelRequest,
    expert = Depends(get_current_expert),
    service: ExpertAppointmentService = Depends(get_expert_appointment_service)
):
    profile_id = expert.get("profile_id")
    if not profile_id:
        raise HTTPException(status_code=403, detail="Expert profile not found in token")
    return await service.cancel_by_expert(appointment_id, profile_id, payload.reason)