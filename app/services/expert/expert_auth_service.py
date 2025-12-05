import logging
import random
from datetime import datetime
from typing import Dict

from fastapi import HTTPException
from bson import ObjectId

from app.models.user_model import User
from app.models.expert_profile_model import ExpertProfile
from app.repositories.user_repository import UserRepository
from app.repositories.expert_repository import ExpertRepository
from app.services.common.email_service import EmailService
from app.core.security import hash_password, verify_password, create_access_token

logger = logging.getLogger(__name__)


class ExpertAuthService:
    """Expert authentication & registration service"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        expert_repo: ExpertRepository,
        email_service: EmailService
    ):
        self.user_repo = user_repo
        self.expert_repo = expert_repo
        self.email_service = email_service
    
    
    async def register_expert(self, data: dict) -> Dict:
        """Phase 1: Create expert account"""
        
        # Check email exists
        existing = await self.user_repo.get_by_email(data["email"])
        if existing:
            logger.warning(f"⚠ Email already registered: {data['email']}")
            raise HTTPException(
                status_code=400,
                detail="Email already exists",
                headers={"X-Error-Code": "E003"}
            )
        
        # Generate temporary username
        temp_username = f"Expert_{random.randint(100000, 999999)}"
        
        # Create user
        user = User(
            email=data["email"],
            username=temp_username,
            password=hash_password(data["password"]),
            role="expert",
            expert_status="pending"
        )
        
        created_user = await self.user_repo.create(user)
        logger.info(f"✓ Expert registered: {created_user.id}")
        
        return {
            "message": "Account created. Please complete your profile.",
            "user_id": str(created_user.id),
            "email": created_user.email,
            "next_step": "complete_profile"
        }
    
    
    async def complete_profile(self, data: dict) -> Dict:
        """Phase 2: Complete expert profile"""
        
        # Validate user exists
        user = await self.user_repo.get_by_id(data["user_id"])
        if not user or user.role != "expert":
            raise HTTPException(
                status_code=404,
                detail="Expert user not found"
            )
        
        # Check no duplicate profile
        if user.expert_profile_id:
            raise HTTPException(
                status_code=409,
                detail="Profile already exists",
                headers={"X-Error-Code": "E015"}
            )
        
        try:
            # Create profile
            profile = ExpertProfile(
                user_id=ObjectId(data["user_id"]),
                full_name=data["full_name"],
                phone=data["phone"],
                date_of_birth=data["date_of_birth"],
                bio=data.get("bio"),
                avatar_url=data.get("avatar_url"),
                years_of_experience=data["years_of_experience"],
                clinic_name=data["clinic_name"],
                clinic_address=data["clinic_address"],
                certificate_url=data["certificate_url"],
                status="pending"
            )
            
            created_profile = await self.expert_repo.create(profile)
            
            # Update user username
            await self.user_repo.update(data["user_id"], {
                "username": data["full_name"],
                "expert_profile_id": created_profile.id,
                "expert_status": "pending"
            })
            
            # Notify admin
            try:
                await self.email_service.notify_admin_new_expert(
                    user.email,
                    data["full_name"]
                )
            except Exception as e:
                logger.warning(f"⚠ Failed to notify admin: {str(e)}")
            
            logger.info(f"✓ Profile created: {created_profile.id}")
            
            return {
                "message": "Profile submitted successfully. Pending approval.",
                "profile_id": str(created_profile.id),
                "username": data["full_name"],
                "status": "pending",
                "estimated_review_time": "24-48 hours"
            }
        
        except Exception as e:
            logger.error(f"✗ Profile creation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create profile"
            )
    
    
    async def login_expert(self, email: str, password: str) -> Dict:
        """Expert login with approval check"""
        
        # Validate credentials
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password):
            logger.warning(f"⚠ Invalid credentials for: {email}")
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials",
                headers={"X-Error-Code": "E009"}
            )
        
        # Check role
        if user.role != "expert":
            raise HTTPException(
                status_code=403,
                detail="Not an expert account"
            )
        
        # Check profile exists
        if not user.expert_profile_id:
            raise HTTPException(
                status_code=403,
                detail="Please complete your profile first"
            )
        
        # Load profile & check status
        profile = await self.expert_repo.get_by_id(str(user.expert_profile_id))
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Expert profile not found. Please contact support"
            )
        
        if profile.status == "pending":
            raise HTTPException(
                status_code=403,
                detail="Account pending approval. Please wait...",
                headers={"X-Error-Code": "E010"}
            )
        
        if profile.status == "rejected":
            raise HTTPException(
                status_code=403,
                detail=f"Application rejected. Reason: {profile.rejection_reason}",
                headers={"X-Error-Code": "E011"}
            )
        
        # Create token
        await self.user_repo.update_last_login(str(user.id), datetime.utcnow())
        
        token = create_access_token({
            "sub": str(user.id),
            "role": "expert",
            "expert_status": "approved",
            "profile_id": str(profile.id),
            "email": user.email
        })
        
        logger.info(f"✓ Expert logged in: {email}")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": user.username,
            "role": "expert",
            "expert_status": "approved",
            "profile_completed": True
        }
