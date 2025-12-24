from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from bson import ObjectId
from typing import List

from app.repositories.user_tree_repository import UserTreeRepository
from app.repositories.positive_action_repository import PositiveActionRepository
from app.repositories.user_repository import UserRepository
from app.models.user_tree_model import UserTree, TreeAction
from app.core.database import get_db

XP_PER_ACTION = 10
BASE_XP_FOR_LEVEL_2 = 50
XP_INCREASE_PER_LEVEL = 25

# Timezone Việt Nam
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

class PositiveActionNotFoundError(Exception): pass
class AlreadyWateredTodayError(Exception): pass
class DatabaseOperationError(Exception): pass

def get_vn_now() -> datetime:
    """Lấy thời gian hiện tại theo giờ Việt Nam (timezone-aware)"""
    return datetime.now(VN_TZ)

def get_vn_date(dt: datetime) -> datetime.date:
    """Convert datetime sang date theo giờ Việt Nam"""
    if dt.tzinfo is None:
        # Nếu naive datetime, coi như UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(VN_TZ).date()

class UserTreeService:
    def __init__(self, tree_repo: UserTreeRepository, action_repo: PositiveActionRepository, user_repo: UserRepository):
        self.tree_repo = tree_repo
        self.action_repo = action_repo
        self.user_repo = user_repo

    def _can_water_today(self, last_watered_at: datetime | None) -> bool:
        """
        Kiểm tra xem có thể tưới cây hôm nay không (theo giờ VN)
        Chỉ cho phép tưới nếu last_watered_date < today_vn
        """
        if not last_watered_at:
            return True
        
        # Lấy ngày hiện tại theo giờ VN
        today_vn = get_vn_now().date()
        
        # Convert last_watered_at sang ngày theo giờ VN
        last_watered_date_vn = get_vn_date(last_watered_at)
        
        # CHỈ cho phép tưới nếu last_watered_date < today
        # Nếu last_watered_date == today => ĐÃ tưới hôm nay => KHÔNG cho tưới
        return last_watered_date_vn < today_vn

    def _calculate_level_details(self, total_xp: int):
        current_level = 1
        xp_for_current_level_start = 0
        xp_needed_for_next_level = BASE_XP_FOR_LEVEL_2

        while True:
            xp_for_next_level_end = xp_for_current_level_start + xp_needed_for_next_level
            if total_xp < xp_for_next_level_end:
                break
            
            current_level += 1
            xp_for_current_level_start = xp_for_next_level_end
            xp_needed_for_next_level += XP_INCREASE_PER_LEVEL

        current_xp_in_level = total_xp - xp_for_current_level_start
        xp_bar_total = xp_needed_for_next_level
        return current_level, current_xp_in_level, xp_bar_total

    def _calculate_streak(self, last_watered_at: datetime | None, current_streak: int) -> int:
        """
        Tính streak theo giờ Việt Nam
        """
        if not last_watered_at:
            return 1
        
        today_vn = get_vn_now().date()
        yesterday_vn = (get_vn_now() - timedelta(days=1)).date()
        last_watered_date_vn = get_vn_date(last_watered_at)
        
        if last_watered_date_vn == yesterday_vn:
            # Tưới liên tiếp (hôm qua tưới, hôm nay tưới)
            return current_streak + 1
        elif last_watered_date_vn < yesterday_vn:
            # Bỏ lỡ ngày, reset streak
            return 1
        else:
            # last_watered_date_vn == today_vn (đã tưới hôm nay)
            # Giữ nguyên streak hiện tại
            return current_streak

    async def get_user_tree_status(self, user_id: ObjectId):
        tree_doc = await self.tree_repo.get_by_user_id(user_id)
        if not tree_doc:
            new_tree = UserTree(user_id=user_id)
            tree_doc = await self.tree_repo.create(new_tree)

        total_xp = tree_doc.get("total_xp", 0)
        level, current_xp, xp_for_next = self._calculate_level_details(total_xp)

        response_data = tree_doc.copy()
        response_data["current_level_calculated"] = level
        response_data["current_xp_in_level"] = current_xp
        response_data["xp_for_next_level"] = xp_for_next
        response_data["can_water_today"] = self._can_water_today(tree_doc.get("last_watered_at"))
        return response_data

    async def nourish_tree(self, user_id: ObjectId, action_id: ObjectId, positive_thoughts: List[str]):
        if not await self.action_repo.get_by_id(action_id):
            raise PositiveActionNotFoundError("Hành động tích cực không tồn tại.")

        tree = await self.tree_repo.get_by_user_id(user_id)
        if not tree:
            tree = await self.get_user_tree_status(user_id)

        # Kiểm tra có thể tưới không (theo giờ VN)
        if not self._can_water_today(tree.get("last_watered_at")):
            raise AlreadyWateredTodayError("Bạn đã tưới cây hôm nay rồi. Hãy quay lại vào ngày mai nhé!")

        new_total_xp = tree.get("total_xp", 0) + XP_PER_ACTION
        new_streak = self._calculate_streak(tree.get("last_watered_at"), tree.get("streak_days", 0))
        formatted_note = "\n".join(f"• {thought}" for thought in positive_thoughts)
        new_action = TreeAction(action_id=action_id, note=formatted_note)

        # Lưu thời gian tưới theo giờ VN (nhưng convert sang UTC để lưu DB)
        vn_now = get_vn_now()
        utc_now = vn_now.astimezone(timezone.utc)

        update_data = {
            "$set": {
                "total_xp": new_total_xp,
                "streak_days": new_streak,
                "last_watered_at": utc_now  # Lưu UTC vào DB
            },
            "$push": {"actions": new_action.model_dump(mode='python')}
        }
        
        if not await self.tree_repo.update(user_id, update_data):
            raise DatabaseOperationError("Không thể cập nhật cây.")
            
        await self.user_repo.increment_total_points(user_id, XP_PER_ACTION)

        return await self.get_user_tree_status(user_id)
    
    async def get_all_positive_actions(self):
        return await self.action_repo.get_all()

def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return UserRepository(db=db)

def get_positive_action_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> PositiveActionRepository:
    return PositiveActionRepository(database=db)

def get_user_tree_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserTreeRepository:
    return UserTreeRepository(database=db)
    
def get_user_tree_service(
    tree_repo: UserTreeRepository = Depends(get_user_tree_repository),
    action_repo: PositiveActionRepository = Depends(get_positive_action_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserTreeService:
    return UserTreeService(tree_repo=tree_repo, action_repo=action_repo, user_repo=user_repo)