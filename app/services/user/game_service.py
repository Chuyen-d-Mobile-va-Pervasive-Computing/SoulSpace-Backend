from fastapi import HTTPException, status
from bson import ObjectId
from typing import List
import logging
from app.models.game_session_model import GameSession
from app.repositories.game_repository import GameRepository
from app.repositories.user_repository import UserRepository
from app.repositories.badge_repository import BadgeRepository
from app.schemas.user.game_schema import (
    GameCompleteRequest,
    GameCompleteResponse,
    BadgeInfo,
    QuestionResponse,
    MatchPairResponse,
    CrosswordWordResponse
)
from app.models.user_badge_model import UserBadge

logger = logging.getLogger(__name__)

class GameService:
    def __init__(
        self,
        game_repo: GameRepository,
        user_repo: UserRepository,
        badge_repo: BadgeRepository
    ):
        self.game_repo = game_repo
        self.user_repo = user_repo
        self.badge_repo = badge_repo

    async def complete_game(
        self, 
        user_id: str, 
        request: GameCompleteRequest
    ) -> GameCompleteResponse:
        """
        ✅ CORE BUSINESS LOGIC: Xử lý hoàn thành minigame
        
        Flow:
        1. Validate user
        2. Lưu game session
        3. Cộng điểm
        4. Check & unlock badges
        5. Return response
        """
        
        # B1. Kiểm tra user tồn tại
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # B2. Lưu game session
        session = GameSession(
            user_id=ObjectId(user_id),
            game_type=request.game_type,
            score=request.score
        )
        await self.game_repo.create_session(session)
        
        logger.info(f"User {user_id} completed game {request.game_type} with score {request.score}")

        # B3. Cộng điểm vào user
        await self.user_repo.update_points(user_id, request.score)
        new_total_points = await self.user_repo.get_user_points(user_id)
        
        logger.info(f"After update, user {user_id} total_points={new_total_points}")

        # B4. Check badges mới unlock
        new_badges = await self._check_and_unlock_badges(user_id, new_total_points)
        
        logger.info(f"New badges for user {user_id}: {[b.name for b in new_badges]}")

        # B5. Return response
        return GameCompleteResponse(
            earned_points=request.score,
            total_points=new_total_points,
            new_badges=[
                BadgeInfo(
                    id=str(badge.id),
                    name=badge.name,
                    description=badge.description,
                    icon=badge.icon,
                    points_required=badge.points_required
                ) for badge in new_badges
            ]
        )

    async def _check_and_unlock_badges(self, user_id: str, total_points: int):
        """
        Kiểm tra và mở khóa badges mới
        
        Logic:
        1. Lấy tất cả badges có points_required <= total_points
        2. Lấy danh sách badges user đã có
        3. Tìm badges chưa có (eligible - owned)
        4. Gán badges mới cho user
        """
        
        logger.info(f"🔍 Checking badges for user {user_id} with {total_points} points")
        
        # Lấy badges đủ điều kiện
        eligible_badges = await self.badge_repo.get_badges_by_points(total_points)
        logger.info(f"   Eligible badges: {[b.name for b in eligible_badges]}")
        
        # Lấy badges user đã có
        user_badges = await self.badge_repo.get_user_badges(user_id)
        owned_badge_ids = {str(ub.badge_id) for ub in user_badges}
        logger.info(f"   Already owned: {len(owned_badge_ids)} badges")
        
        # Tìm badges mới (chưa có)
        new_badges = [
            badge for badge in eligible_badges
            if str(badge.id) not in owned_badge_ids
        ]
        
        logger.info(f"   New badges to unlock: {[b.name for b in new_badges]}")
        
        # Gán badges mới cho user
        for badge in new_badges:
            user_badge = UserBadge(
                user_id=ObjectId(user_id),
                badge_id=badge.id
            )
            result = await self.badge_repo.create_user_badge(user_badge)
            if result:
                logger.info(f"   ✅ Unlocked: {badge.name}")
            else:
                logger.warning(f"   ⚠️  Failed to unlock: {badge.name} (duplicate?)")
        
        logger.info(f"✅ Badge check completed. Unlocked {len(new_badges)} new badges")
        return new_badges

    async def get_questions(self) -> List[QuestionResponse]:
        """Lấy danh sách câu hỏi cho Choose game"""
        questions = await self.game_repo.get_questions()
        return [
            QuestionResponse(
                id=str(q.id),
                question=q.question,
                correct_answer=q.correct_answer,
                options=q.options,
                meaning=q.meaning
            ) for q in questions
        ]

    async def get_match_pairs(self) -> List[MatchPairResponse]:
        """Lấy cặp từ cho Match game"""
        pairs = await self.game_repo.get_match_pairs()
        return [
            MatchPairResponse(
                id=str(p.id),
                word=p.word,
                meaning=p.meaning
            ) for p in pairs
        ]

    async def get_crossword_words(self) -> List[CrosswordWordResponse]:
        """Lấy từ vựng cho Crossword game"""
        words = await self.game_repo.get_crossword_words()
        return [
            CrosswordWordResponse(
                id=str(w.id),
                word=w.word,
                clue=w.clue
            ) for w in words
        ]
