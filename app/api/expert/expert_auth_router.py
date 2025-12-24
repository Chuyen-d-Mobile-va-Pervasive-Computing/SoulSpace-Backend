from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.schemas.expert.expert_schema import (
    ExpertProfileUpdate,
    ExpertRegister,
    ExpertProfileCreate,
    FileUploadResponse
)
from app.schemas.user.auth_schema import UserLogin
from app.services.expert.expert_auth_service import ExpertAuthService
from app.services.common.cloudinary_service import CloudinaryService
from app.core.dependencies import get_current_user, get_expert_auth_service, get_cloudinary_service

router = APIRouter(prefix="/auth/expert", tags=["Expert Auth"])


@router.post("/register", status_code=201)
async def register_expert(
    data: ExpertRegister,
    service: ExpertAuthService = Depends(get_expert_auth_service)
):
    """Expert sign up - Phase 1"""
    return await service.register_expert(data.dict())


@router.post("/complete-profile", status_code=200)
async def complete_expert_profile(
    data: ExpertProfileCreate,
    service: ExpertAuthService = Depends(get_expert_auth_service)
):
    """Complete profile - Phase 2"""
    return await service.complete_profile(data.dict())

@router.patch("/profile", status_code=200)
async def update_profile(
    payload: ExpertProfileUpdate,
    current_user: dict = Depends(get_current_user),
    service: ExpertAuthService = Depends(get_expert_auth_service)
):
    """
    Update expert profile information.
    Chỉ gửi những trường cần thay đổi.
    """
    user_id = str(current_user["_id"])
    
    # exclude_unset=True giúp loại bỏ các trường người dùng không gửi lên
    update_data = payload.model_dump(exclude_unset=True)
    
    return await service.update_expert_profile(user_id, update_data)

@router.post("/login", status_code=200)
async def login_expert(
    credentials: UserLogin,
    service: ExpertAuthService = Depends(get_expert_auth_service)
):
    """Expert login (requires approved status)"""
    return await service.login_expert(credentials.email, credentials.password)


