"""
Expert role API endpoints.
These endpoints are for expert-only operations.
"""
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.core.permissions import Role, require_role

router = APIRouter(prefix="/expert", tags=["👨‍⚕️ Expert - Consultation (Chuyên gia)"])


@router.get("/health")
async def expert_health_check():
    """
    Health check endpoint for expert routes.
    This is a placeholder for future expert functionality.
    """
    return {
        "status": "healthy",
        "role": "expert",
        "message": "Expert routes are ready for implementation"
    }


@router.get("/info")
@require_role(Role.EXPERT)
async def expert_info(current_user: dict = Depends(get_current_user)):
    """
    Get expert-specific information.
    This endpoint requires expert role.
    """
    return {
        "message": "Expert access granted",
        "user": current_user.get("username", "unknown"),
        "role": current_user.get("role", "unknown")
    }
