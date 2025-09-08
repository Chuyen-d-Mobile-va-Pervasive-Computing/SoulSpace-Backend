from fastapi import APIRouter, Depends
from app.schemas.auth_schema import UserRegister, UserLogin, UserResponse, ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.repositories.user_repository import UserRepository
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_service(db=Depends(get_db)):
    user_repo = UserRepository(db)
    email_service = EmailService()
    return AuthService(user_repo, email_service)

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, service: AuthService = Depends(get_auth_service)):
    return await service.register(user_data)

@router.post("/login")
async def login(user_data: UserLogin, service: AuthService = Depends(get_auth_service)):
    token = await service.login(user_data.email, user_data.password)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(forgot_data: ForgotPasswordRequest, service: AuthService = Depends(get_auth_service)):
    await service.forgot_password(forgot_data)
    return {"message": "OTP sent to email"}

@router.post("/reset-password")
async def reset_password(reset_data: ResetPasswordRequest, service: AuthService = Depends(get_auth_service)):
    await service.reset_password(reset_data)
    return {"message": "Password reset successfully"}

@router.post("/change-password")
async def change_password(
    change_data: ChangePasswordRequest,
    service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user)
):
    await service.change_password(str(current_user["_id"]), change_data)
    return {"message": "Password changed successfully"}