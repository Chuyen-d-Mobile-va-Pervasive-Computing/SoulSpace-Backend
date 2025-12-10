from functools import lru_cache
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.config import settings
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from app.core.database import get_db
from app.repositories.test_repository import TestRepository
from app.repositories.user_test_result_repository import UserTestResultRepository
from app.repositories.user_repository import UserRepository
from app.repositories.expert_repository import ExpertRepository
from app.repositories.expert_schedule_repository import ExpertScheduleRepository
from app.repositories.expert_schedule_repository import ExpertScheduleRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.services.common.email_service import EmailService
from app.services.common.cloudinary_service import CloudinaryService
from app.services.expert.expert_auth_service import ExpertAuthService
from app.services.admin.admin_expert_service import AdminExpertService
from app.services.user.expert_service import UserExpertService
from app.services.expert.expert_schedule_service import ExpertScheduleService
from app.services.user.appointment_service import UserAppointmentService
from app.repositories.payment_repository import PaymentRepository
from app.services.user.payment_service import UserPaymentService
from app.repositories.expert_wallet_repository import ExpertWalletRepository
from app.services.expert.dashboard_service import ExpertDashboardService

oauth2_scheme = HTTPBearer()
oauth2_scheme_optional = HTTPBearer(auto_error=False)

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
        expert_obj = {"_id": ObjectId(user_id), "role": role}
        # Nếu là expert, trả về cả profile_id nếu có
        if role == "expert" and "profile_id" in payload:
            expert_obj["profile_id"] = payload["profile_id"]
        return expert_obj
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme_optional)
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.
    Use this for endpoints that work for both authenticated and unauthenticated users.
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        
        if user_id is None or role is None:
            return None
        return {"_id": ObjectId(user_id), "role": role}
    except JWTError:
        return None


async def get_current_admin(
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
        if role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"_id": ObjectId(user_id), "role": role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Expert role dependency
async def get_current_expert(user=Depends(get_current_user)):
    if user["role"] != "expert":
        raise HTTPException(status_code=403, detail="Not expert")
    return user
        
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

def get_expert_schedule_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> ExpertScheduleRepository:
    return ExpertScheduleRepository(db)

def get_user_expert_service(
    expert_repo: ExpertRepository = Depends(get_expert_repository),
    schedule_repo: ExpertScheduleRepository = Depends(get_expert_schedule_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserExpertService:
    return UserExpertService(expert_repo, schedule_repo, user_repo)

def get_expert_schedule_repository(db: AsyncIOMotorDatabase = Depends(get_database)):
    return ExpertScheduleRepository(db)

def get_expert_schedule_service(
    repo: ExpertScheduleRepository = Depends(get_expert_schedule_repository),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ExpertScheduleService:
    return ExpertScheduleService(repo, db)

def get_appointment_repository(db: AsyncIOMotorDatabase = Depends(get_database)):
    return AppointmentRepository(db)

def get_payment_repository(db: AsyncIOMotorDatabase = Depends(get_database)):
    return PaymentRepository(db)

def get_user_payment_service(
    payment_repo=Depends(get_payment_repository),
    appointment_repo=Depends(get_appointment_repository),
    expert_repo=Depends(get_expert_repository),
    email_service=Depends(get_email_service)
) -> UserPaymentService:
    return UserPaymentService(payment_repo, appointment_repo, expert_repo, email_service)

def get_expert_appointment_service(
    appointment_repo=Depends(get_appointment_repository),
    payment_repo=Depends(get_payment_repository),
    user_repo=Depends(get_user_repository),
    expert_repo=Depends(get_expert_repository),
    email_service=Depends(get_email_service)
):
    from app.services.expert.appointment_service import ExpertAppointmentService
    return ExpertAppointmentService(appointment_repo, payment_repo, user_repo, expert_repo, email_service)

def get_user_appointment_service(
    appointment_repo=Depends(get_appointment_repository),
    expert_repo=Depends(get_expert_repository),
    payment_repo=Depends(get_payment_repository),
    email_service=Depends(get_email_service)
) -> UserAppointmentService:
    return UserAppointmentService(appointment_repo, expert_repo, payment_repo, email_service)

def get_expert_wallet_repository(db: AsyncIOMotorDatabase = Depends(get_database)):
    return ExpertWalletRepository(db)

def get_expert_dashboard_service(
    appointment_repo=Depends(get_appointment_repository),
    expert_repo=Depends(get_expert_repository),
    wallet_repo=Depends(get_expert_wallet_repository),
    user_repo=Depends(get_user_repository)
) -> ExpertDashboardService:
    return ExpertDashboardService(appointment_repo, expert_repo, wallet_repo, user_repo)