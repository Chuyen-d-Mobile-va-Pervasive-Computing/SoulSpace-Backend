from app.repositories.test_question_repository import TestQuestionRepository
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends
from app.core.database import get_db
import logging
from datetime import datetime
from fastapi import Depends
from bson import ObjectId
from typing import List

from app.core.database import get_db
from app.repositories.test_repository import TestRepository
from app.repositories.user_test_result_repository import UserTestResultRepository
from app.repositories.test_question_repository import TestQuestionRepository
from app.schemas.user.user_test_result_schema import SubmitTestPayloadSchema
from app.core.dependencies import get_test_repository, get_user_test_result_repository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestNotFoundError(Exception): pass
class ResultNotFoundError(Exception): pass
class NotOwnerOfResultError(Exception): pass
class TestAlreadyCompletedError(Exception): pass
class AnswerCountMismatchError(Exception): pass
class InvalidOptionError(Exception): pass
class DatabaseOperationError(Exception): pass

class UserTestResultService:
    def __init__(self, result_repo: UserTestResultRepository, test_repo: TestRepository, question_repo: TestQuestionRepository):
        self.result_repo = result_repo
        self.test_repo = test_repo
        self.question_repo = question_repo

    async def submit_test(self, user_id: ObjectId, test_code: str, answers: List[dict]):
        # Lấy test và câu hỏi snapshot
        test = await self.test_repo.get_test_by_code(test_code)
        if not test or test.get("is_deleted"):
            raise ValueError("Test not found or deleted.")
        questions = await self.question_repo.get_questions_by_test_id(test["_id"], include_deleted=False)
        # Validate số lượng câu trả lời
        if len(answers) != len(questions):
            raise ValueError("Answer count mismatch.")
        # Tính điểm, snapshot
        total_score = 0
        snapshot_questions = []
        for q, a in zip(questions, answers):
            option = next((opt for opt in q["options"] if str(opt.get("option_id", opt.get("_id"))) == str(a["selected_option_id"])), None)
            if not option:
                raise ValueError(f"Invalid option for question {q['_id']}")
            total_score += option["score_value"] if "score_value" in option else option["score"]
            snapshot_questions.append({
                "question_id": q["_id"],
                "question_text": q["question_text"],
                "selected_option_id": a["selected_option_id"],
                "selected_option_text": option["option_text"],
                "score": option["score_value"] if "score_value" in option else option["score"]
            })
        result_level = "Severe" if total_score >= test["severe_threshold"] else "Normal"
        feedback = test["expert_recommendation"] if result_level == "Severe" else ""
        snapshot = {
            "test_title": test["title"],
            "test_code": test["test_code"],
            "questions": snapshot_questions
        }
        result_data = {
            "user_id": user_id,
            "test_id": test["_id"],
            "test_snapshot": snapshot,
            "total_score": total_score,
            "result_level": result_level,
            "feedback": feedback,
            "completed_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        return await self.result_repo.create_result(result_data)

    async def get_result_detail(self, result_id: ObjectId):
        from app.utils.convert import convert_objectid_to_str
        result = await self.result_repo.get_result_by_id(result_id)
        return convert_objectid_to_str(result)

def get_test_question_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TestQuestionRepository:
    return TestQuestionRepository(database=db)

# --- Dependency Injection  ---
def get_user_test_result_service(
    test_repo: TestRepository = Depends(get_test_repository),
    result_repo: UserTestResultRepository = Depends(get_user_test_result_repository),
    question_repo: TestQuestionRepository = Depends(get_test_question_repository)
) -> UserTestResultService:
    return UserTestResultService(result_repo=result_repo, test_repo=test_repo, question_repo=question_repo)

