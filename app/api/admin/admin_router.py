"""
Admin role API endpoints.
These endpoints are for admin-only operations.
"""
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.core.permissions import Role, require_role

router = APIRouter(prefix="/admin", tags=["🔧 Admin - Management (Quản trị)"])


@router.get("/health")
async def admin_health_check():
    """
    Health check endpoint for admin routes.
    This is a placeholder for future admin functionality.
    """
    return {
        "status": "healthy",
        "role": "admin",
        "message": "Admin routes are ready for implementation"
    }


@router.get("/info")
@require_role(Role.ADMIN)
async def admin_info(current_user: dict = Depends(get_current_user)):
    """
    Get admin-specific information.
    This endpoint requires admin role.
    """
    return {
        "message": "Admin access granted",
        "user": current_user.get("username", "unknown"),
        "role": current_user.get("role", "unknown")
    }
