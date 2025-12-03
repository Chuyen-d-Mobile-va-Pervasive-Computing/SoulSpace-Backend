from fastapi import HTTPException, status
from typing import List
from app.repositories.badge_repository import BadgeRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user.badge_schema import (
    UserBadgeResponse,
    BadgeResponse,
    AllBadgesResponse
)

class BadgeService:
    def __init__(
        self,
        badge_repo: BadgeRepository,
        user_repo: UserRepository
    ):
        self.badge_repo = badge_repo
        self.user_repo = user_repo

    async def get_user_badges(self, user_id: str) -> List[UserBadgeResponse]:
        """
        Lấy danh sách badges user đã sở hữu
        
        Returns:
            List[UserBadgeResponse]: Badges với thông tin chi tiết
        """
        # Kiểm tra user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Lấy user_badges
        user_badges = await self.badge_repo.get_user_badges(user_id)
        
        # Join với badges để lấy thông tin chi tiết
        result = []
        for ub in user_badges:
            badge = await self.badge_repo.get_badge_by_id(str(ub.badge_id))
            if badge:
                result.append(UserBadgeResponse(
                    badge_id=str(badge.id),
                    name=badge.name,
                    description=badge.description,
                    icon=badge.icon,
                    points_required=badge.points_required,
                    earned_at=ub.earned_at.isoformat()
                ))
        
        return result

    async def get_all_badges_status(self, user_id: str) -> AllBadgesResponse:
        """
        Lấy tất cả badges (earned + locked)
        
        Returns:
            AllBadgesResponse: 
            - earned_badges: Badges đã mở khóa
            - locked_badges: Badges chưa mở khóa
        """
        # Lấy tất cả badges
        all_badges = await self.badge_repo.get_all_badges()
        
        # Lấy badges user đã có
        user_badges = await self.badge_repo.get_user_badges(user_id)
        owned_badge_ids = {str(ub.badge_id) for ub in user_badges}
        
        # Phân loại
        earned = []
        locked = []
        
        for badge in all_badges:
            if str(badge.id) in owned_badge_ids:
                # Tìm earned_at
                ub = next(ub for ub in user_badges if str(ub.badge_id) == str(badge.id))
                earned.append(UserBadgeResponse(
                    badge_id=str(badge.id),
                    name=badge.name,
                    description=badge.description,
                    icon=badge.icon,
                    points_required=badge.points_required,
                    earned_at=ub.earned_at.isoformat()
                ))
            else:
                locked.append(BadgeResponse(
                    id=str(badge.id),
                    name=badge.name,
                    description=badge.description,
                    icon=badge.icon,
                    points_required=badge.points_required,
                    order=badge.order
                ))
        
        return AllBadgesResponse(
            earned_badges=earned,
            locked_badges=locked,
            total_earned=len(earned),
            total_badges=len(all_badges)
        )
