from fastapi import HTTPException, status
from datetime import datetime, timedelta
from app.models.user_model import User
from app.schemas.user.auth_schema import (
    UserRegister, UserResponse, ForgotPasswordRequest, 
    ResetPasswordRequest, ChangePasswordRequest, 
    UpdateUsernameRequest, TokenResponse, UpdateProfileRequest
)
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.services.common.email_service import EmailService
import random
import string

class AuthService:
    def __init__(self, user_repo: UserRepository, email_service: EmailService):
        self.user_repo = user_repo
        self.email_service = email_service
        self.prefixes = ["Soul", "Zen", "Mind", "Calm", "Spirit", "Dream", "Luna", "Inner", "Aura", "Echo"]
        self.concepts = ["Sky", "Ocean", "Leaf", "Peace", "Glow", "River", "Dawn", "Hope", "Wave", "Balance"]

    async def generate_username(self):
        max_attempts = 10
        for _ in range(max_attempts):
            prefix = random.choice(self.prefixes)
            concept = random.choice(self.concepts)
            number = random.randint(1, 9999)
            username = f"{prefix}{concept}_{number:04d}"
            existing_user = await self.user_repo.get_by_username(username)
            if not existing_user:
                return username
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to generate a unique username after multiple attempts")

    async def register(self, user_data: UserRegister) -> UserResponse:
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

        # Check phone if provided
        if user_data.phone:
            existing_phone = await self.user_repo.db.users.find_one({"phone": user_data.phone})
            if existing_phone:
                raise HTTPException(status_code=400, detail="Phone number is already in use")

        username = await self.generate_username()
        user = User(
            username=username,
            email=user_data.email,
            password=hash_password(user_data.password),
            phone=user_data.phone,
            role="user"
        )
        try:
            created_user = await self.user_repo.create(user)
            return UserResponse(
                username=created_user.username,
                email=created_user.email,
                phone=created_user.phone,
                role=created_user.role,
                created_at=created_user.created_at.isoformat(),
                total_points=created_user.total_points
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        try:
            await self.user_repo.update_last_login(str(user.id), datetime.utcnow())
            token_payload = {"sub": str(user.id), "role": user.role}
            access_token = create_access_token(token_payload)
            return TokenResponse(
                access_token=access_token, 
                username=user.username, # Trả về username
                role=user.role
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to login: {str(e)}")

    async def forgot_password(self, forgot_data: ForgotPasswordRequest):
        user = await self.user_repo.get_by_email(forgot_data.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
        
        otp = ''.join(random.choices(string.digits, k=6))
        expiry = datetime.utcnow() + timedelta(minutes=10)
        
        try:
            await self.user_repo.update_reset_otp(str(user.id), otp, expiry)
            await self.email_service.send_otp_email(forgot_data.email, otp)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process forgot password: {str(e)}")

    async def reset_password(self, reset_data: ResetPasswordRequest):
        user = await self.user_repo.get_by_email(reset_data.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
        
        if not user.reset_otp or user.reset_otp != reset_data.otp or user.reset_otp_expiry < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
        
        try:
            await self.user_repo.update(str(user.id), {"password": hash_password(reset_data.new_password)})
            await self.user_repo.clear_reset_otp(str(user.id))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to reset password: {str(e)}")

    async def change_password(self, user_id: str, change_data: ChangePasswordRequest):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not verify_password(change_data.old_password, user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password")

        try:
            await self.user_repo.update(user_id, {"password": hash_password(change_data.new_password)})
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to change password: {str(e)}")

    async def update_username(self, user_id: str, update_data: UpdateUsernameRequest):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        existing_user = await self.user_repo.get_by_username(update_data.new_username)
        if existing_user and str(existing_user.id) != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

        try:
            await self.user_repo.update(user_id, {"username": update_data.new_username})
            return {"message": "Username updated successfully", "username": update_data.new_username}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update username: {str(e)}")

    async def update_avatar(self, user_id: str, avatar_url: str):
        """Cập nhật avatar cho user."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        try:
            await self.user_repo.update(user_id, {"avatar_url": avatar_url})
            return {"message": "Avatar updated successfully", "avatar_url": avatar_url}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update avatar: {str(e)}")

    async def update_profile(self, user_id: str, update_data: UpdateProfileRequest):
        """Cập nhật thông tin profile (username, avatar)."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        update_fields = {}
        
        # Check username nếu có thay đổi
        if update_data.username:
            existing_user = await self.user_repo.get_by_username(update_data.username)
            if existing_user and str(existing_user.id) != user_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
            update_fields["username"] = update_data.username
        
        # Check avatar
        if update_data.avatar_url:
            update_fields["avatar_url"] = update_data.avatar_url

        if not update_fields:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

        try:
            await self.user_repo.update(user_id, update_fields)
            return {
                "message": "Profile updated successfully",
                "updated_fields": list(update_fields.keys())
            }
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update profile: {str(e)}")

    async def get_user_profile(self, user_id: str):
        """Lấy thông tin profile của user."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "avatar_url": getattr(user, 'avatar_url', None),
            "total_points": user.total_points,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
        }

