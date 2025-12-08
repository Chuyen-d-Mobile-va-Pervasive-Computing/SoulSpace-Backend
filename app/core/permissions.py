"""
Role-based permissions and access control for SoulSpace Backend.
"""
from enum import Enum
from functools import wraps
from typing import List
from fastapi import HTTPException, status, Depends
from app.core.dependencies import get_current_user


class Role(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    EXPERT = "expert"


def require_role(*allowed_roles: Role):
    """
    Decorator to enforce role-based access control on endpoints.
    
    Usage:
        @router.get("/admin-only")
        @require_role(Role.ADMIN)
        async def admin_endpoint(current_user = Depends(get_current_user)):
            ...
    
    Args:
        *allowed_roles: Variable number of Role enum values that are allowed to access the endpoint
        
    Raises:
        HTTPException: 403 Forbidden if user's role is not in allowed_roles
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs (injected by endpoint's Depends)
            current_user = kwargs.get("current_user")
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = current_user.get("role", "user")
            
            # Convert allowed_roles to strings for comparison
            allowed_role_strings = [role.value for role in allowed_roles]
            
            if user_role not in allowed_role_strings:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_role_strings)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_role(user: dict, *allowed_roles: Role) -> bool:
    """
    Check if a user has one of the allowed roles.
    
    Args:
        user: User dictionary containing role information
        *allowed_roles: Variable number of Role enum values to check against
        
    Returns:
        bool: True if user has an allowed role, False otherwise
    """
    user_role = user.get("role", "user")
    allowed_role_strings = [role.value for role in allowed_roles]
    return user_role in allowed_role_strings
