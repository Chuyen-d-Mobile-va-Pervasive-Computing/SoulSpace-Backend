# app/services/user/user_test_result_service.py
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

    async def _get_and_validate_test_doc(self, test_code: str):
        test_doc = await self.test_repo.get_test_by_code(test_code)
        if not test_doc or test_doc.get("is_deleted"):
            raise TestNotFoundError(f"Test with code '{test_code}' not found or deleted.")
        return test_doc

    async def _process_answers_payload(self, test_code: str, test_id: ObjectId, payload: SubmitTestPayloadSchema):
        all_questions = await self.question_repo.get_questions_by_test_id(test_id, include_deleted=False)
        questions_map = {str(q["_id"]): q for q in all_questions}
        processed_answers = []
        for ans in payload.answers:
            question_id_str = str(ans.question_id)
            question = questions_map.get(question_id_str)
            if not question:
                raise InvalidOptionError(f"Question ID {question_id_str} does not belong to test {test_code}.")
            chosen_option = next((opt for opt in question["options"] if str(opt.get("option_id", opt.get("_id"))) == str(ans.chosen_option_id)), None)
            if not chosen_option:
                raise InvalidOptionError(f"Option ID {ans.chosen_option_id} is not valid for question ID {question_id_str}.")
            processed_answers.append({
                "question_id": ObjectId(ans.question_id),
                "option_id": ObjectId(ans.chosen_option_id),
                "score_value": chosen_option["score"] if "score" in chosen_option else chosen_option.get("score_value", 0)
            })
        return processed_answers

    async def save_test_progress(self, user_id: ObjectId, test_code: str, payload: SubmitTestPayloadSchema):
        test_doc = await self._get_and_validate_test_doc(test_code)
        newly_processed_answers = await self._process_answers_payload(test_code, test_doc["_id"], payload)
        in_progress_doc = await self.result_repo.find_in_progress_result(ObjectId(user_id), ObjectId(test_doc["_id"]))
        if in_progress_doc:
            existing_answers = {str(ans['question_id']): ans for ans in in_progress_doc.get('answers', [])}
            for new_ans in newly_processed_answers:
                existing_answers[str(new_ans['question_id'])] = new_ans
            final_answers = list(existing_answers.values())
            await self.result_repo.update_answers(in_progress_doc["_id"], final_answers)
            return await self.result_repo.get_by_id(in_progress_doc["_id"])
        else:
            draft_data = {
                "user_id": ObjectId(user_id),
                "test_id": ObjectId(test_doc["_id"]),
                "status": "in-progress",
                "started_at": datetime.utcnow(),
                "answers": newly_processed_answers,
                "completed_at": None,
                "total_score": None,
                "severity_level": None,
                "result_label": None,
                "guidance_notes": None,
                "needs_expert": None,
                "test_snapshot": None,
                "result_level": None,
                "feedback": None
            }
            inserted_id = await self.result_repo.create_result(draft_data)
            return await self.result_repo.get_by_id(inserted_id)

    async def submit_test(self, user_id: ObjectId, test_code: str, payload: SubmitTestPayloadSchema):
        # First, check if there's an in-progress draft and finalize it
        test_doc = await self._get_and_validate_test_doc(test_code)
        in_progress_doc = await self.result_repo.find_in_progress_result(ObjectId(user_id), ObjectId(test_doc["_id"]))
        if in_progress_doc:
            # Merge with new answers if any
            existing_answers = {str(ans['question_id']): ans for ans in in_progress_doc.get('answers', [])}
            newly_processed_answers = await self._process_answers_payload(test_code, test_doc["_id"], payload)
            for new_ans in newly_processed_answers:
                existing_answers[str(new_ans['question_id'])] = new_ans
            final_answers = list(existing_answers.values())
            if len(final_answers) != len(await self.question_repo.get_questions_by_test_id(test_doc["_id"], include_deleted=False)):
                raise AnswerCountMismatchError("Incomplete answers for submission.")
            # Calculate and update
            total_score = sum(ans['score_value'] for ans in final_answers)
            result_level = "Severe" if total_score >= test_doc["severe_threshold"] else "Normal"
            feedback = test_doc["expert_recommendation"] if result_level == "Severe" else ""
            snapshot_questions = []
            questions = await self.question_repo.get_questions_by_test_id(test_doc["_id"], include_deleted=False)
            for ans in final_answers:
                q = next((qq for qq in questions if str(qq["_id"]) == str(ans["question_id"])), None)
                opt = next((oo for oo in q["options"] if str(oo.get("option_id", oo.get("_id"))) == str(ans["option_id"])), None)
                snapshot_questions.append({
                    "question_id": ans["question_id"],
                    "question_text": q["question_text"],
                    "selected_option_id": str(ans["option_id"]),
                    "selected_option_text": opt["option_text"],
                    "score": ans["score_value"]
                })
            snapshot = {
                "test_title": test_doc["title"],
                "test_code": test_doc["test_code"],
                "questions": snapshot_questions
            }
            final_data = {
                "test_snapshot": snapshot,
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "total_score": total_score,
                "result_level": result_level,
                "feedback": feedback,
                "answers": final_answers  # Optional, can remove if not needed for completed
            }
            await self.result_repo.update_result(in_progress_doc["_id"], final_data)
            return await self.result_repo.get_by_id(in_progress_doc["_id"])
        else:
            # No draft, submit new
            processed_answers = await self._process_answers_payload(test_code, test_doc["_id"], payload)
            if len(processed_answers) != len(await self.question_repo.get_questions_by_test_id(test_doc["_id"], include_deleted=False)):
                raise AnswerCountMismatchError("Incomplete answers for submission.")
            total_score = sum(ans['score_value'] for ans in processed_answers)
            result_level = "Severe" if total_score >= test_doc["severe_threshold"] else "Normal"
            feedback = test_doc["expert_recommendation"] if result_level == "Severe" else ""
            snapshot_questions = []
            questions = await self.question_repo.get_questions_by_test_id(test_doc["_id"], include_deleted=False)
            for ans in processed_answers:
                q = next((qq for qq in questions if str(qq["_id"]) == str(ans["question_id"])), None)
                opt = next((oo for oo in q["options"] if str(oo.get("option_id", oo.get("_id"))) == str(ans["option_id"])), None)
                snapshot_questions.append({
                    "question_id": ans["question_id"],
                    "question_text": q["question_text"],
                    "selected_option_id": str(ans["option_id"]),
                    "selected_option_text": opt["option_text"],
                    "score": ans["score_value"]
                })
            snapshot = {
                "test_title": test_doc["title"],
                "test_code": test_doc["test_code"],
                "questions": snapshot_questions
            }
            result_data = {
                "user_id": user_id,
                "test_id": test_doc["_id"],
                "test_snapshot": snapshot,
                "status": "completed",
                "started_at": datetime.utcnow(),
                "completed_at": datetime.utcnow(),
                "total_score": total_score,
                "result_level": result_level,
                "feedback": feedback,
                "answers": processed_answers, # Optional
                "created_at": datetime.utcnow()
            }
            inserted_id = await self.result_repo.create_result(result_data)
            return await self.result_repo.get_by_id(inserted_id)
    async def get_result_detail(self, result_id: ObjectId):
        from app.utils.convert import convert_objectid_to_str
        result = await self.result_repo.get_result_by_id(result_id)
        return convert_objectid_to_str(result)
def get_test_question_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TestQuestionRepository:
    return TestQuestionRepository(database=db)
# --- Dependency Injection ---
def get_user_test_result_service(
    test_repo: TestRepository = Depends(get_test_repository),
    result_repo: UserTestResultRepository = Depends(get_user_test_result_repository),
    question_repo: TestQuestionRepository = Depends(get_test_question_repository)
) -> UserTestResultService:
    return UserTestResultService(result_repo=result_repo, test_repo=test_repo, question_repo=question_repo)