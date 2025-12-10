import logging
from datetime import datetime
from typing import Dict

from fastapi import HTTPException
from bson import ObjectId

from app.repositories.user_repository import UserRepository
from app.repositories.expert_repository import ExpertRepository
from app.services.common.email_service import EmailService

logger = logging.getLogger(__name__)


class AdminExpertService:
    """Admin service for managing experts"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        expert_repo: ExpertRepository,
        email_service: EmailService
    ):
        self.user_repo = user_repo
        self.expert_repo = expert_repo
        self.email_service = email_service
    
    
    async def get_all_experts(self, status: str = None) -> Dict:
        """Get all experts, optionally filter by status"""
        
        profiles = await self.expert_repo.get_all(status=status)
        
        # Build response with user info
        experts = []
        for profile in profiles:
            user = await self.user_repo.get_by_id(str(profile.user_id))
            
            created_at = profile.created_at
            updated_at = profile.updated_at
            approval_date = profile.approval_date
            
            experts.append({
                "user_id": str(profile.user_id),
                "email": user.email if user else None,
                "profile_id": str(profile.id),
                "full_name": profile.full_name,
                "phone": profile.phone,
                "date_of_birth": profile.date_of_birth,
                "years_of_experience": profile.years_of_experience,
                "clinic_name": profile.clinic_name,
                "clinic_address": profile.clinic_address,
                "certificate_url": profile.certificate_url,
                "avatar_url": profile.avatar_url,
                "bio": profile.bio,
                "status": profile.status,
                "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else created_at,
                "updated_at": updated_at.isoformat() if hasattr(updated_at, 'isoformat') else updated_at,
                "approval_date": approval_date.isoformat() if approval_date and hasattr(approval_date, 'isoformat') else approval_date
            })
        
        return {
            "total": len(experts),
            "experts": experts
        }
    
    
    async def get_expert_by_user_id(self, user_id: str):
        """Get expert profile by user_id - useful for experts to get their own profile_id"""
        return await self.expert_repo.get_by_user_id(user_id)
    
    
    async def get_expert_detail(self, profile_id: str) -> Dict:
        """Get expert detail by profile_id"""
        
        profile = await self.expert_repo.get_by_id(profile_id)
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Expert profile not found"
            )
        
        # Get user info
        user = await self.user_repo.get_by_id(str(profile.user_id))
        
        created_at = profile.created_at
        updated_at = profile.updated_at
        approval_date = profile.approval_date
        
        return {
            "user_id": str(profile.user_id),
            "email": user.email if user else None,
            "profile_id": str(profile.id),
            "full_name": profile.full_name,
            "phone": profile.phone,
            "date_of_birth": profile.date_of_birth,
            "bio": profile.bio,
            "avatar_url": profile.avatar_url,
            "years_of_experience": profile.years_of_experience,
            "clinic_name": profile.clinic_name,
            "clinic_address": profile.clinic_address,
            "certificate_url": profile.certificate_url,
            "status": profile.status,
            "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else created_at,
            "updated_at": updated_at.isoformat() if hasattr(updated_at, 'isoformat') else updated_at,
            "approval_date": approval_date.isoformat() if approval_date and hasattr(approval_date, 'isoformat') else approval_date,
            "approved_by": str(profile.approved_by) if profile.approved_by else None,
            "rejection_reason": profile.rejection_reason
        }
    
    
    async def approve_expert(self, profile_id: str, admin_id: str) -> Dict:
        """Approve expert"""
        
        profile = await self.expert_repo.get_by_id(profile_id)
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found"
            )
        
        if profile.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Profile already processed. Current status: {profile.status}"
            )
        
        # Update profile
        await self.expert_repo.update(profile_id, {
            "status": "approved",
            "approval_date": datetime.utcnow(),
            "approved_by": ObjectId(admin_id),
            "updated_at": datetime.utcnow()
        })
        
        # Update user
        await self.user_repo.update(str(profile.user_id), {
            "expert_status": "approved"
        })
        
        # Notify expert
        user = await self.user_repo.get_by_id(str(profile.user_id))
        try:
            await self.email_service.notify_expert_approved(
                user.email,
                profile.full_name
            )
        except Exception as e:
            logger.warning(f"⚠ Failed to notify expert: {str(e)}")
        
        logger.info(f"✓ Expert approved: {profile_id}")
        
        return {
            "message": "Expert approved successfully",
            "profile_id": profile_id,
            "expert_email": user.email,
            "expert_name": profile.full_name
        }
    
    
    async def reject_expert(self, profile_id: str, admin_id: str, reason: str = None) -> Dict:
        """Reject expert"""
        
        profile = await self.expert_repo.get_by_id(profile_id)
        if not profile or profile.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Invalid profile or already processed"
            )
        
        # Update profile
        await self.expert_repo.update(profile_id, {
            "status": "rejected",
            "rejection_reason": reason or "Not specified",
            "updated_at": datetime.utcnow()
        })
        
        # Update user
        await self.user_repo.update(str(profile.user_id), {
            "expert_status": "rejected"
        })
        
        # Notify expert
        user = await self.user_repo.get_by_id(str(profile.user_id))
        try:
            await self.email_service.notify_expert_rejected(
                user.email,
                profile.full_name,
                reason
            )
        except Exception as e:
            logger.warning(f"⚠ Failed to notify expert: {str(e)}")
        
        logger.info(f"✓ Expert rejected: {profile_id}")
        
        return {
            "message": "Expert rejected",
            "profile_id": profile_id,
            "expert_email": user.email,
            "reason": reason
        }
