from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.user.appointment_schema import (
    AppointmentCreateRequest,
    AppointmentCreateResponse,
    AppointmentListResponse,
    AppointmentDetailResponse, 
    AppointmentCancelRequest,
    AppointmentCancelResponse
)
from app.services.user.appointment_service import UserAppointmentService
from app.core.dependencies import get_current_user, get_user_appointment_service

router = APIRouter(prefix="/appointments", tags=["User - Appointments"])

@router.post("/", response_model=AppointmentCreateResponse, status_code=201)
async def create_appointment(
    payload: AppointmentCreateRequest,
    current_user = Depends(get_current_user),
    service: UserAppointmentService = Depends(get_user_appointment_service)
):
    user_id = str(current_user["_id"])
    return await service.create_appointment(user_id, payload.expert_profile_id, payload.schedule_id)

@router.get("/", response_model=AppointmentListResponse)
async def get_appointment_list(
    status: str = Query(None, regex="^(pending|upcoming|past|cancelled)$"),
    current_user = Depends(get_current_user),
    service: UserAppointmentService = Depends(get_user_appointment_service)
):
    return await service.get_appointment_list(str(current_user["_id"]), status)

@router.get("/{appointment_id}", response_model=AppointmentDetailResponse)
async def get_appointment_detail(
    appointment_id: str,
    current_user = Depends(get_current_user),
    service: UserAppointmentService = Depends(get_user_appointment_service)
):
    return await service.get_appointment_detail(appointment_id, str(current_user["_id"]))

@router.delete("/{appointment_id}", response_model=AppointmentCancelResponse)
async def cancel_appointment(
    appointment_id: str,
    payload: AppointmentCancelRequest,
    current_user = Depends(get_current_user),
    service: UserAppointmentService = Depends(get_user_appointment_service)
):
    return await service.cancel_appointment(appointment_id, str(current_user["_id"]), payload.cancel_reason)