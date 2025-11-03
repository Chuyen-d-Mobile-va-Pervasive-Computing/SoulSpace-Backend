import logging
from datetime import datetime
from fastapi import Depends
from bson import ObjectId

from app.core.database import get_db
from app.repositories.test_repository import TestRepository
from app.repositories.user_test_result_repository import UserTestResultRepository
from app.schemas.user_test_result_schema import SubmitTestPayloadSchema
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
    def __init__(self, test_repo: TestRepository, result_repo: UserTestResultRepository):
        self.test_repo = test_repo
        self.result_repo = result_repo

    async def _get_and_validate_test_doc(self, test_code: str):
        test_doc = await self.test_repo.get_test_by_code(test_code)
        if not test_doc:
            raise TestNotFoundError(f"Test with code '{test_code}' not found.")
        return test_doc

    async def _process_answers_payload(self, test_code: str, test_id: ObjectId, payload: SubmitTestPayloadSchema):
        all_questions = await self.test_repo.get_questions_by_test_id(test_id)
        questions_map = {str(q["_id"]): q for q in all_questions}

        processed_answers = []
        for ans in payload.answers:
            question_id_str = str(ans.question_id)
            question = questions_map.get(question_id_str)
            if not question:
                raise InvalidOptionError(f"Question ID {question_id_str} does not belong to test {test_code}.")

            chosen_option = next((opt for opt in question["options"] if str(opt["option_id"]) == str(ans.chosen_option_id)), None)
            if not chosen_option:
                raise InvalidOptionError(f"Option ID {ans.chosen_option_id} is not valid for question ID {question_id_str}.")

            processed_answers.append({
                "question_id": ObjectId(ans.question_id),
                "option_id": ObjectId(ans.chosen_option_id),
                "score_value": chosen_option["score_value"]
            })
        return processed_answers

    def _calculate_final_result_data(self, test_doc: dict, processed_answers: list) -> dict:
            total_score = sum(ans['score_value'] for ans in processed_answers)

            needs_expert = total_score >= test_doc["severe_threshold"]
            if needs_expert:
                severity_level = "Severe"
                result_label = f"High risk - Score: {total_score}"
                guidance = f"{test_doc['self_care_guidance']} {test_doc['expert_recommendation']}"
            else:
                severity_level = "Normal/Mild"
                result_label = f"Low risk - Score: {total_score}"
                guidance = test_doc["self_care_guidance"]

            return {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "answers": processed_answers,
                "total_score": total_score,
                "severity_level": severity_level,
                "result_label": result_label,
                "guidance_notes": guidance,
                "needs_expert": needs_expert
            }
    async def submit_completed_test(self, user_id: ObjectId, test_code: str, payload: SubmitTestPayloadSchema):
        test_doc = await self._get_and_validate_test_doc(test_code)

        if len(payload.answers) != test_doc["num_questions"]:
            raise AnswerCountMismatchError(f"Submission requires exactly {test_doc['num_questions']} answers.")

        processed_answers = await self._process_answers_payload(test_doc["test_code"], test_doc["_id"], payload)
        final_data = self._calculate_final_result_data(test_doc, processed_answers)

        in_progress_doc = await self.result_repo.find_in_progress_result(ObjectId(user_id), ObjectId(test_doc["_id"]))

        if in_progress_doc:
            logger.info(f"Finalizing existing draft {in_progress_doc['_id']} for user {user_id}")
            result = await self.result_repo.find_and_finalize_result(in_progress_doc["_id"], final_data)
            if result:
                result["test_code"] = test_doc["test_code"]
            return result

        else:
            logger.info(f"Creating new completed result for user {user_id}")
            new_result_document = {
                "user_id": ObjectId(user_id),
                "test_id": ObjectId(test_doc["_id"]),
                "started_at": datetime.utcnow(),
                **final_data
            }
            result = await self.result_repo.create_result(new_result_document)
            if result:
                result["test_code"] = test_doc["test_code"]
            return result


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
            result = await self.result_repo.get_by_id(in_progress_doc["_id"])
            if result:
                result["test_code"] = test_doc["test_code"]
            return result
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
                "needs_expert": None
            }
            result = await self.result_repo.create_draft(draft_data)
            if result:
                result["test_code"] = test_doc["test_code"]
            return result

    async def finalize_test_result(self, user_id: ObjectId, result_id: ObjectId, payload: SubmitTestPayloadSchema):
        result_doc = await self.result_repo.get_by_id(result_id)
        if not result_doc:
            raise ResultNotFoundError(f"Test result with ID {result_id} not found.")
        if result_doc["user_id"] != ObjectId(user_id):
            raise NotOwnerOfResultError("User is not the owner of this test result.")
        if result_doc["status"] == "completed":
            raise TestAlreadyCompletedError("This test has already been completed.")

        test_doc = await self.test_repo.get_by_id(result_doc["test_id"])

        if len(payload.answers) != test_doc["num_questions"]:
            raise AnswerCountMismatchError(f"Submission requires exactly {test_doc['num_questions']} answers.")

        final_processed_answers = await self._process_answers_payload(test_doc["test_code"], test_doc["_id"], payload)

        total_score = sum(ans['score_value'] for ans in final_processed_answers)

        needs_expert = total_score >= test_doc["severe_threshold"]
        if needs_expert:
            severity_level = "Severe"
            result_label = f"High risk - Score: {total_score}"
            guidance = f"{test_doc['self_care_guidance']} {test_doc['expert_recommendation']}"
        else:
            severity_level = "Normal/Mild"
            result_label = f"Low risk - Score: {total_score}"
            guidance = test_doc["self_care_guidance"]

        final_data = {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "answers": final_processed_answers,
            "total_score": total_score,
            "severity_level": severity_level,
            "result_label": result_label,
            "guidance_notes": guidance,
            "needs_expert": needs_expert
        }

        return await self.result_repo.find_and_finalize_result(result_id, final_data)

    async def get_user_completed_tests_summary(self, user_id: ObjectId):
        try:
            return await self.result_repo.get_latest_completed_results_by_user(user_id)
        except Exception as e:
            logger.error(f"Database error in get_user_completed_tests_summary: {e}")
            raise DatabaseOperationError("Could not fetch completed test summaries.")
            
    async def get_result_details(self, result_id: ObjectId, user_id: ObjectId):
        # 1. Lấy document kết quả
        result_doc = await self.result_repo.get_by_id(result_id)
        if not result_doc:
            raise ResultNotFoundError(f"Test result with ID {result_id} not found.")
        
        # 2. Kiểm tra quyền sở hữu
        if result_doc["user_id"] != user_id:
            raise NotOwnerOfResultError("User is not the owner of this test result.")

        # 3. Lấy thông tin bài test (test_name, test_code)
        test_doc = await self.test_repo.get_by_id(result_doc["test_id"])
        if not test_doc:
            # Trường hợp hiếm gặp: kết quả tồn tại nhưng test đã bị xóa
            raise TestNotFoundError(f"Associated test with ID {result_doc['test_id']} not found.")

        # 4. Lấy tất cả câu hỏi của bài test để map
        all_questions = await self.test_repo.get_questions_by_test_id(test_doc["_id"])
        questions_map = {}
        for q in all_questions:
            options_map = {str(opt["option_id"]): opt["option_text"] for opt in q["options"]}
            questions_map[str(q["_id"])] = {
                "question_text": q["question_text"],
                "options": options_map
            }

        # 5. Xây dựng response chi tiết
        answered_questions_details = []
        for answer in result_doc.get("answers", []):
            q_id_str = str(answer["question_id"])
            opt_id_str = str(answer["option_id"])
            
            question_info = questions_map.get(q_id_str)
            if question_info:
                chosen_option_text = question_info["options"].get(opt_id_str, "N/A")
                answered_questions_details.append({
                    "question_text": question_info["question_text"],
                    "chosen_option_text": chosen_option_text,
                    "score_value": answer["score_value"]
                })

        # Giả định max_score = num_questions * 3
        max_score = test_doc.get("num_questions", 0) * 3

        # 6. Gộp thông tin và trả về
        response_data = {
            **result_doc,
            "test_name": test_doc["test_name"],
            "test_code": test_doc["test_code"],
            "max_score": max_score,
            "answered_questions": answered_questions_details
        }
        return response_data
# --- Dependency Injection  ---
def get_user_test_result_service(
    test_repo: TestRepository = Depends(get_test_repository),
    result_repo: UserTestResultRepository = Depends(get_user_test_result_repository)
) -> UserTestResultService:
    return UserTestResultService(test_repo=test_repo, result_repo=result_repo)
