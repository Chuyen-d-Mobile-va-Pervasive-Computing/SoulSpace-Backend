from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.permissions import Role, require_role
from app.core.dependencies import get_current_user, get_expert_service

router = APIRouter(prefix="/admin/experts", tags=["🔧 Admin Expert"])


@router.post("/{profile_id}/approve")
@require_role(Role.ADMIN)
async def approve_expert(
    profile_id: str,
    current_user: dict = Depends(get_current_user),
    service = Depends(get_expert_service)
):
    """Approve expert registration"""
    admin_id = str(current_user["_id"])
    return await service.approve_expert(profile_id, admin_id)


@router.post("/{profile_id}/reject")
@require_role(Role.ADMIN)
async def reject_expert(
    profile_id: str,
    reason: str = Query(None),
    current_user: dict = Depends(get_current_user),
    service = Depends(get_expert_service)
):
    """Reject expert registration"""
    admin_id = str(current_user["_id"])
    return await service.reject_expert(profile_id, admin_id, reason)


@router.get("/all")
@require_role(Role.ADMIN)
async def get_all_experts(
    status: str = Query(None, description="Filter by status: pending, approved, rejected"),
    current_user: dict = Depends(get_current_user),
    service = Depends(get_expert_service)
):
    """Get all experts, optionally filter by status"""
    return await service.get_all_experts(status=status)


@router.get("/{profile_id}")
@require_role(Role.ADMIN)
async def get_expert_detail(
    profile_id: str,
    current_user: dict = Depends(get_current_user),
    service = Depends(get_expert_service)
):
    """Get expert detail by profile_id"""
    return await service.get_expert_detail(profile_id)
