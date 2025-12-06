from functools import lru_cache
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.config import settings
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_db
from app.repositories.test_repository import TestRepository
from app.repositories.user_test_result_repository import UserTestResultRepository
from app.repositories.user_repository import UserRepository
from app.repositories.expert_repository import ExpertRepository
from app.services.common.email_service import EmailService
from app.services.common.cloudinary_service import CloudinaryService
from app.services.expert.expert_auth_service import ExpertAuthService
from app.services.admin.admin_expert_service import AdminExpertService

oauth2_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        
        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"_id": ObjectId(user_id), "role": role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_test_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TestRepository:
    return TestRepository(database=db)

def get_user_test_result_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserTestResultRepository:
    return UserTestResultRepository(database=db)


# ===== Expert dependencies =====

def get_database(db: AsyncIOMotorDatabase = Depends(get_db)) -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db


def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> UserRepository:
    """Get user repository"""
    return UserRepository(db=db)


@lru_cache()
def get_email_service() -> EmailService:
    """Email service singleton"""
    return EmailService()


@lru_cache()
def get_cloudinary_service() -> CloudinaryService:
    """Cloudinary service singleton"""
    return CloudinaryService()


def get_expert_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> ExpertRepository:
    """Expert repository"""
    return ExpertRepository(db=db)


def get_expert_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    expert_repo: ExpertRepository = Depends(get_expert_repository),
    email_service: EmailService = Depends(get_email_service)
) -> ExpertAuthService:
    """Expert authentication service"""
    return ExpertAuthService(user_repo, expert_repo, email_service)


def get_admin_expert_service(
    user_repo: UserRepository = Depends(get_user_repository),
    expert_repo: ExpertRepository = Depends(get_expert_repository),
    email_service: EmailService = Depends(get_email_service)
) -> AdminExpertService:
    """Admin expert management service"""
    return AdminExpertService(user_repo, expert_repo, email_service)


# Backward compatibility
def get_expert_service(
    user_repo: UserRepository = Depends(get_user_repository),
    expert_repo: ExpertRepository = Depends(get_expert_repository),
    email_service: EmailService = Depends(get_email_service)
) -> AdminExpertService:
    """Expert service (backward compatibility - returns AdminExpertService)"""
    return AdminExpertService(user_repo, expert_repo, email_service)