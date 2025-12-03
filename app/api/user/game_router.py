from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.user.game_schema import (
    GameCompleteRequest,
    GameCompleteResponse,
    QuestionResponse,
    MatchPairResponse,
    CrosswordWordResponse,
    UserPointsResponse
)
from app.services.user.game_service import GameService
from app.repositories.game_repository import GameRepository
from app.repositories.user_repository import UserRepository
from app.repositories.badge_repository import BadgeRepository
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/game", tags=["👤 User - Games (Trò chơi)"])

def get_game_service(db=Depends(get_db)):
    game_repo = GameRepository(db)
    user_repo = UserRepository(db)
    badge_repo = BadgeRepository(db)
    return GameService(game_repo, user_repo, badge_repo)

# ===== MINIGAME DATA ENDPOINTS =====

@router.get("/choose/questions", response_model=List[QuestionResponse])
async def get_choose_questions(
    service: GameService = Depends(get_game_service)
):
    """
    Lấy danh sách câu hỏi cho minigame Choose
    
    - FE gọi khi load màn hình Choose game
    - Trả về tất cả câu hỏi active
    """
    return await service.get_questions()

@router.get("/match/pairs", response_model=List[MatchPairResponse])
async def get_match_pairs(
    service: GameService = Depends(get_game_service)
):
    """
    Lấy danh sách cặp từ cho minigame Match
    
    - FE gọi khi load màn hình Match game
    - FE shuffle options ở client side
    """
    return await service.get_match_pairs()

@router.get("/crossword/words", response_model=List[CrosswordWordResponse])
async def get_crossword_words(
    service: GameService = Depends(get_game_service)
):
    """
    Lấy từ vựng cho minigame Crossword
    
    - FE gọi khi load màn hình Crossword game
    - FE generate grid layout ở client side
    """
    return await service.get_crossword_words()

# ===== CORE ENDPOINT =====

@router.post("/complete", response_model=GameCompleteResponse)
async def complete_game(
    request: GameCompleteRequest,
    service: GameService = Depends(get_game_service),
    current_user: dict = Depends(get_current_user)
):
    """
    ✅✅ API CHÍNH QUAN TRỌNG NHẤT ✅✅
    
    Xử lý khi user hoàn thành minigame
    
    Flow:
    1. FE tính điểm (choose: correct*10, match: total*20, crossword: 50)
    2. FE gọi API này với game_type, score
    3. BE lưu session, cộng điểm, check badge
    4. BE trả về earned_points, total_points, new_badges
    5. FE hiển thị popup "Bạn nhận được +X điểm" + "Mở khóa badge Y!"
    
    Request body:
    {
      "game_type": "choose",
      "score": 10
    }
    
    Response:
    {
      "earned_points": 10,
      "total_points": 50,
      "new_badges": [
        {
          "id": "...",
          "name": "PathFinder",
          "description": "Earn 10 points",
          "icon": "pathfinder",
          "points_required": 10
        }
      ]
    }
    """
    # Sử dụng user_id từ JWT (bảo mật hơn)
    user_id = str(current_user["_id"])
    
    return await service.complete_game(user_id, request)

# ===== USER STATS ENDPOINTS =====

@router.get("/user/{user_id}/points", response_model=UserPointsResponse)
async def get_user_points(
    user_id: str,
    service: GameService = Depends(get_game_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy tổng điểm của user
    
    - Authorization: User chỉ có thể xem điểm của chính mình
    """
    # Check authorization
    if str(current_user["_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to view this user's points"
        )
    
    total_points = await service.user_repo.get_user_points(user_id)
    
    return UserPointsResponse(
        user_id=user_id,
        total_points=total_points
    )
