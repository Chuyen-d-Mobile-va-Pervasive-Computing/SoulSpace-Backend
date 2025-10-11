from fastapi import HTTPException, status
from datetime import datetime, timedelta
from app.models.user_model import User
from app.schemas.auth_schema import UserRegister, UserResponse, ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest, UpdateUsernameRequest
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.services.email_service import EmailService
import random
import string

class AuthService:
    def __init__(self, user_repo: UserRepository, email_service: EmailService):
        """Initialize AuthService with a user repository and email service."""
        self.user_repo = user_repo
        self.email_service = email_service
        # Định nghĩa danh sách prefix và concept
        self.prefixes = ["Soul", "Zen", "Mind", "Calm", "Spirit", "Dream", "Luna", "Inner", "Aura", "Echo"]
        self.concepts = ["Sky", "Ocean", "Leaf", "Peace", "Glow", "River", "Dawn", "Hope", "Wave", "Balance"]

    async def generate_username(self):
        """Generate a unique random username."""
        max_attempts = 10  # Giới hạn số lần thử để tránh lặp vô hạn
        for _ in range(max_attempts):
            prefix = random.choice(self.prefixes)
            concept = random.choice(self.concepts)
            number = random.randint(1, 9999)
            username = f"{prefix}{concept}_{number:04d}"  # Sử dụng 4 chữ số để tránh trùng lặp
            # Kiểm tra trùng lặp username
            existing_user = await self.user_repo.get_by_username(username)
            if not existing_user:
                return username
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to generate a unique username after multiple attempts")

    async def register(self, user_data: UserRegister) -> UserResponse:
        """Register a new user."""
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        
        username = await self.generate_username()
        user = User(
            username=username,
            email=user_data.email,
            password=hash_password(user_data.password)
        )
        try:
            created_user = await self.user_repo.create(user)
            return UserResponse(
                username=created_user.username,
                email=created_user.email,
                created_at=created_user.created_at.isoformat(),
                total_points=created_user.total_points
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to register user: {str(e)}")

    async def login(self, email: str, password: str) -> str:
        """Authenticate a user and return a JWT token."""
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        try:
            await self.user_repo.update_last_login(str(user.id), datetime.utcnow())
            return create_access_token({"sub": str(user.id)})
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to login: {str(e)}")

    async def forgot_password(self, forgot_data: ForgotPasswordRequest):
        """Generate and send OTP for password reset."""
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
        """Reset password using OTP."""
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
        """Change user password."""
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
        """Update the user's username."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Kiểm tra username mới có tồn tại không
        existing_user = await self.user_repo.get_by_username(update_data.new_username)
        if existing_user and str(existing_user.id) != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

        try:
            await self.user_repo.update(user_id, {"username": update_data.new_username})
            return {"message": "Username updated successfully", "username": update_data.new_username}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update username: {str(e)}")