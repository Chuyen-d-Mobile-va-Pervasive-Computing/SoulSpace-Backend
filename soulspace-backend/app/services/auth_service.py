from fastapi import HTTPException, status
from datetime import datetime
from app.models.user_model import User
from app.schemas.auth_schema import UserRegister, UserResponse
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token

class AuthService:
    def __init__(self, user_repo: UserRepository):
        """Initialize AuthService with a user repository."""
        self.user_repo = user_repo

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
            username=user_data.username,
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