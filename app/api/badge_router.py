from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.badge_schema import (
    UserBadgeResponse,
    AllBadgesResponse
)
from app.services.badge_service import BadgeService
from app.repositories.badge_repository import BadgeRepository
from app.repositories.user_repository import UserRepository
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/badges", tags=["Badges"])

def get_badge_service(db=Depends(get_db)):
    badge_repo = BadgeRepository(db)
    user_repo = UserRepository(db)
    return BadgeService(badge_repo, user_repo)

@router.get("/user/{user_id}", response_model=List[UserBadgeResponse])
async def get_user_badges(
    user_id: str,
    service: BadgeService = Depends(get_badge_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy danh sách badges user đã sở hữu
    
    - FE gọi để hiển thị "My Badges"
    - Chỉ trả về badges đã mở khóa
    
    Response:
    [
      {
        "badge_id": "66f100...",
        "name": "PathFinder",
        "description": "Earn 10 points",
        "icon": "pathfinder",
        "points_required": 10,
        "earned_at": "2025-09-22T04:45:20.011Z"
      }
    ]
    """
    # Check authorization
    if str(current_user["_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to view this user's badges"
        )
    
    return await service.get_user_badges(user_id)

@router.get("/user/{user_id}/all", response_model=AllBadgesResponse)
async def get_all_badges_status(
    user_id: str,
    service: BadgeService = Depends(get_badge_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy tất cả badges (earned + locked)
    
    - FE gọi để hiển thị toàn bộ badges system
    - Earned: Đã mở khóa (màu sắc bình thường)
    - Locked: Chưa mở khóa (màu xám #CCCCCC)
    
    Response:
    {
      "earned_badges": [ ... ],
      "locked_badges": [ ... ],
      "total_earned": 1,
      "total_badges": 6
    }
    """
    # Check authorization
    if str(current_user["_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to view this user's badges"
        )
    
    return await service.get_all_badges_status(user_id)
