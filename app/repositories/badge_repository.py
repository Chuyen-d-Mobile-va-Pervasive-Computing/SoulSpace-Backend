from fastapi import HTTPException, status
from bson import ObjectId
from typing import List, Optional
import logging
from app.models.badge_model import Badge
from app.models.user_badge_model import UserBadge

logger = logging.getLogger(__name__)

class BadgeRepository:
    def __init__(self, db):
        self.db = db
        # NOTE: Indexes should be created via migration scripts
        # Motor cannot create indexes in sync __init__ method

    async def get_all_badges(self) -> List[Badge]:
        """Lấy tất cả badges"""
        try:
            cursor = self.db.badges.find({}).sort("order", 1)
            badges = await cursor.to_list(length=100)
            return [Badge(**b) for b in badges]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch badges: {str(e)}"
            )

    async def get_badges_by_points(self, points: int) -> List[Badge]:
        """Lấy badges có points_required <= points"""
        try:
            cursor = self.db.badges.find({"points_required": {"$lte": points}})
            badges = await cursor.to_list(length=100)
            return [Badge(**b) for b in badges]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch badges by points: {str(e)}"
            )

    async def get_user_badges(self, user_id: str) -> List[UserBadge]:
        """Lấy tất cả badges của user"""
        try:
            logger.info(f"🔍 Getting user_badges for user_id={user_id}")
            
            # Try both string and ObjectId formats for compatibility
            cursor = self.db.user_badges.find({
                "$or": [
                    {"user_id": user_id},  # String format
                    {"user_id": ObjectId(user_id)}  # ObjectId format
                ]
            })
            user_badges = await cursor.to_list(length=100)
            logger.info(f"   Found {len(user_badges)} user_badges in database")
            
            if user_badges:
                logger.info(f"   Sample: {user_badges[0]}")
            
            result = [UserBadge(**ub) for ub in user_badges]
            logger.info(f"   Converted to {len(result)} UserBadge objects")
            return result
        except Exception as e:
            logger.error(f"❌ Error fetching user badges: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch user badges: {str(e)}"
            )

    async def create_user_badge(self, user_badge: UserBadge) -> Optional[UserBadge]:
        """Gán badge cho user"""
        try:
            logger.info(f"   Attempting to create user_badge: user_id={user_badge.user_id}, badge_id={user_badge.badge_id}")
            result = await self.db.user_badges.insert_one(user_badge.dict(by_alias=True))
            user_badge.id = result.inserted_id
            logger.info(f"   ✅ Successfully created user_badge with _id={result.inserted_id}")
            return user_badge
        except Exception as e:
            # Duplicate key error (user đã có badge này)
            if "duplicate key" in str(e).lower():
                logger.warning(f"   ⚠️  Duplicate badge detected: user_id={user_badge.user_id}, badge_id={user_badge.badge_id}")
                return None
            logger.error(f"   ❌ Error creating user_badge: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user badge: {str(e)}"
            )

    async def get_badge_by_id(self, badge_id: str) -> Optional[Badge]:
        """Lấy badge theo ID"""
        try:
            badge_data = await self.db.badges.find_one({"_id": ObjectId(badge_id)})
            return Badge(**badge_data) if badge_data else None
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch badge: {str(e)}"
            )
