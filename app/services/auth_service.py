from fastapi import HTTPException, status
from datetime import datetime, timedelta
from app.models.user_model import User
from app.schemas.auth_schema import UserRegister, UserResponse, ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest
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

    async def register(self, user_data: UserRegister) -> UserResponse:
        """Register a new user.

        Args:
            user_data: User registration data.

        Raises:
            HTTPException: If email exists or database error occurs.

        Returns:
            UserResponse: Registered user details.
        """
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        
        user = User(
            email=user_data.email,
            password=hash_password(user_data.password)
        )
        try:
            created_user = await self.user_repo.create(user)
            return UserResponse(
                email=created_user.email,
                created_at=created_user.created_at.isoformat(),
                total_points=created_user.total_points
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to register user: {str(e)}")

    async def login(self, email: str, password: str) -> str:
        """Authenticate a user and return a JWT token.

        Args:
            email: User email.
            password: User password.

        Raises:
            HTTPException: If credentials are invalid or database error occurs.

        Returns:
            str: JWT access token.
        """
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        try:
            await self.user_repo.update_last_login(str(user.id), datetime.utcnow())
            return create_access_token({"sub": str(user.id)})
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to login: {str(e)}")

    async def forgot_password(self, forgot_data: ForgotPasswordRequest):
        """Generate and send OTP for password reset.

        Args:
            forgot_data: Email for password reset.

        Raises:
            HTTPException: If email not found or error occurs.
        """
        user = await self.user_repo.get_by_email(forgot_data.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
        
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        expiry = datetime.utcnow() + timedelta(minutes=10)
        
        try:
            await self.user_repo.update_reset_otp(str(user.id), otp, expiry)
            await self.email_service.send_otp_email(forgot_data.email, otp)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process forgot password: {str(e)}")

    async def reset_password(self, reset_data: ResetPasswordRequest):
        """Reset password using OTP.

        Args:
            reset_data: Email, OTP, and new password.

        Raises:
            HTTPException: If email not found, OTP invalid/expired, or error occurs.
        """
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
        """Change user password.

        Args:
            user_id: ID of the authenticated user.
            change_data: Old password, new password, and confirmation.

        Raises:
            HTTPException: If old password is incorrect, passwords don't match, or database error occurs.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not verify_password(change_data.old_password, user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password")

        try:
            await self.user_repo.update(user_id, {"password": hash_password(change_data.new_password)})
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to change password: {str(e)}")