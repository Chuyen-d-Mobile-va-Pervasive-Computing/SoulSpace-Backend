from bson import ObjectId
from datetime import datetime
from typing import List, Dict
from fastapi import HTTPException, status 
from app.repositories.user_test_result_repository import UserTestResultRepository
from app.repositories.test_repository import TestRepository
from app.schemas.user.user_test_result_schema import SubmitTestPayloadSchema, UserTestResultDetailSchema, AnswerDetailSchema

class TestNotFoundError(Exception): pass
class ResultNotFoundError(Exception): pass
class NotOwnerOfResultError(Exception): pass
class AnswerCountMismatchError(Exception): pass
class InvalidOptionError(Exception): pass

class UserTestResultService:
    def __init__(self, result_repo: UserTestResultRepository, test_repo: TestRepository):
        self.result_repo = result_repo
        self.test_repo = test_repo

    async def _prepare_answers_with_snapshot(self, test_id: ObjectId, test_code: str, payload_answers: List) -> List[Dict]:
        """Validate và tạo snapshot câu trả lời"""
        
        # Lấy tất cả câu hỏi của bài test này
        questions_db = await self.test_repo.get_questions_by_test_id(test_id)
        
        # Tạo map với key là STRING ID để so sánh cho chuẩn
        questions_map = {str(q["_id"]): q for q in questions_db}

        processed_answers = []
        
        for ans in payload_answers:
            q_id_str = str(ans.question_id)
            
            if q_id_str not in questions_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Question ID {q_id_str} does not belong to test {test_code} (Test ID: {test_id})"
                )

            question_doc = questions_map[q_id_str]
            
            # Tìm option
            selected_option = next((opt for opt in question_doc["options"] if str(opt["_id"]) == str(ans.chosen_option_id)), None)
            
            if not selected_option:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Option ID {ans.chosen_option_id} is not valid for question {q_id_str}"
                )

            processed_answers.append({
                "question_id": ans.question_id,
                "option_id": ans.chosen_option_id,
                "score_value": selected_option["score_value"],
                "question_text": question_doc["question_text"],
                "chosen_option_text": selected_option["option_text"]
            })
            
        return processed_answers

    async def save_test_progress(self, user_id: ObjectId, test_code: str, payload: SubmitTestPayloadSchema):
        test = await self.test_repo.get_test_by_code(test_code)
        if not test or test.get("is_deleted"):
            raise TestNotFoundError(f"Test {test_code} not found")
        
        snapshot_answers = await self._prepare_answers_with_snapshot(test["_id"], test_code, payload.answers)

        existing_draft = await self.result_repo.find_in_progress_result(user_id, test["_id"])
        
        if existing_draft:
            await self.result_repo.update_answers(existing_draft["_id"], snapshot_answers)
            return await self.result_repo.get_by_id(existing_draft["_id"])
        else:
            draft_data = {
                "user_id": user_id,
                "test_id": test["_id"],
                "test_code": test["test_code"],
                "status": "in-progress",
                "answers": snapshot_answers,
                "started_at": datetime.utcnow()
            }
            return await self.result_repo.create_draft(draft_data)

    async def submit_completed_test(self, user_id: ObjectId, test_code: str, payload: SubmitTestPayloadSchema):
        test = await self.test_repo.get_test_by_code(test_code)
        if not test or test.get("is_deleted"):
            raise TestNotFoundError(f"Test {test_code} not found")

        snapshot_answers = await self._prepare_answers_with_snapshot(test["_id"], test_code, payload.answers)
        
        if len(snapshot_answers) != test["num_questions"]:
             raise AnswerCountMismatchError(f"Expected {test['num_questions']} answers, got {len(snapshot_answers)}")

        total_score = sum(a["score_value"] for a in snapshot_answers)
        
        severity = "Normal"
        if total_score >= test["severe_threshold"]:
            severity = "High/Severe"
        
        final_data = {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "answers": snapshot_answers,
            "total_score": total_score,
            "severity_level": severity,
            "result_label": severity, 
            "guidance_notes": test["expert_recommendation"] if severity == "High/Severe" else test["self_care_guidance"],
            "needs_expert": severity == "High/Severe"
        }

        existing_draft = await self.result_repo.find_in_progress_result(user_id, test["_id"])
        
        if existing_draft:
            return await self.result_repo.find_and_finalize_result(existing_draft["_id"], final_data)
        else:
            final_data.update({
                "user_id": user_id,
                "test_id": test["_id"],
                "test_code": test["test_code"],
                "started_at": datetime.utcnow()
            })
            return await self.result_repo.create_result(final_data)
    
    async def get_user_completed_tests_summary(self, user_id: ObjectId):
        return await self.result_repo.get_latest_completed_results_by_user(user_id)

    async def get_result_details(self, result_id: ObjectId, user_id: ObjectId) -> UserTestResultDetailSchema:
        result = await self.result_repo.get_by_id(result_id)
        if not result:
            raise ResultNotFoundError("Result not found")
        if result["user_id"] != user_id:
             raise NotOwnerOfResultError("Access denied")

        test_info = await self.test_repo.get_by_id(result["test_id"])
        test_name = test_info["title"] if test_info else "Unknown Test"
        max_score = (test_info["num_questions"] * 3) if test_info else 0 

        answered_details = []
        for ans in result.get("answers", []):
            answered_details.append(AnswerDetailSchema(
                question_text=ans.get("question_text", "Question text unavailable"), 
                chosen_option_text=ans.get("chosen_option_text", "Option text unavailable"), 
                score_value=ans.get("score_value", 0)
            ))

        return UserTestResultDetailSchema(
            **result,
            test_name=test_name,
            max_score=max_score,
            answered_questions=answered_details
        )
    
    async def get_current_progress(self, user_id: ObjectId, test_code: str) -> Dict | None:
        test = await self.test_repo.get_test_by_code(test_code)
        if not test:
            raise TestNotFoundError(f"Test {test_code} not found")

        draft = await self.result_repo.find_in_progress_result(user_id, test["_id"])
        return draft

# DI Helper
from app.repositories.test_repository import TestRepository
from app.core.database import get_db
from fastapi import Depends

def get_user_test_result_service(db=Depends(get_db)) -> UserTestResultService:
    test_repo = TestRepository(db)
    result_repo = UserTestResultRepository(db)
    return UserTestResultService(result_repo, test_repo)