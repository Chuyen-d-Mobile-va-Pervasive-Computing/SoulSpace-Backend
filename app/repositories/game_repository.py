from fastapi import HTTPException, status
from bson import ObjectId
from typing import List
from app.models.game_session_model import GameSession
from app.models.game_question_model import GameQuestion
from app.models.match_pair_model import MatchPair
from app.models.crossword_word_model import CrosswordWord

class GameRepository:
    def __init__(self, db):
        self.db = db
        # NOTE: Indexes should be created via migration scripts
        # Motor cannot create indexes in sync __init__ method

    async def create_session(self, session: GameSession) -> GameSession:
        """Lưu game session"""
        try:
            result = await self.db.game_sessions.insert_one(session.dict(by_alias=True))
            session.id = result.inserted_id
            return session
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create game session: {str(e)}"
            )

    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[GameSession]:
        """Lấy lịch sử chơi của user"""
        try:
            cursor = self.db.game_sessions.find({
                "$or": [
                    {"user_id": user_id},  # String format
                    {"user_id": ObjectId(user_id)}  # ObjectId format
                ]
            }).sort("created_at", -1).limit(limit)
            sessions = await cursor.to_list(length=limit)
            return [GameSession(**session) for session in sessions]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch sessions: {str(e)}"
            )

    async def get_questions(self) -> List[GameQuestion]:
        """Lấy tất cả câu hỏi active"""
        try:
            cursor = self.db.game_questions.find({"is_active": True}).sort("order", 1)
            questions = await cursor.to_list(length=100)
            return [GameQuestion(**q) for q in questions]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch questions: {str(e)}"
            )

    async def get_match_pairs(self) -> List[MatchPair]:
        """Lấy tất cả cặp từ active"""
        try:
            cursor = self.db.match_pairs.find({"is_active": True}).sort("order", 1)
            pairs = await cursor.to_list(length=100)
            return [MatchPair(**p) for p in pairs]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch pairs: {str(e)}"
            )

    async def get_crossword_words(self) -> List[CrosswordWord]:
        """Lấy tất cả từ crossword active"""
        try:
            cursor = self.db.crossword_words.find({"is_active": True}).sort("order", 1)
            words = await cursor.to_list(length=100)
            return [CrosswordWord(**w) for w in words]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch words: {str(e)}"
            )
