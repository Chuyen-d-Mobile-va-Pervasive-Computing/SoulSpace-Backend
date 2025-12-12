# app/services/admin/test_service.py
from fastapi import Depends
from app.repositories.test_repository import TestRepository
from app.repositories.test_question_repository import TestQuestionRepository
from bson import ObjectId
from datetime import datetime
from typing import List
from app.core.dependencies import get_test_repository, get_question_repository
from app.utils.convert import convert_objectid_to_str
import logging

logger = logging.getLogger(__name__)

class AdminTestService:
    def __init__(self, test_repo: TestRepository, question_repo: TestQuestionRepository):
        self.test_repo = test_repo
        self.question_repo = question_repo

    async def _normalize_orders_and_options(self, questions: List[dict]):
        """Tự động gán order và option_id cho toàn bộ questions"""
        for q_idx, q in enumerate(questions, start=1):
            # GÁN LẠI question_order THEO THỨ TỰ MẢNG (quan trọng nhất!)
            q["question_order"] = q_idx

            for o_idx, opt in enumerate(q.get("options", []), start=1):
                opt["option_order"] = o_idx
                if not opt.get("option_id"):
                    opt["option_id"] = str(ObjectId())
                else:
                    opt["option_id"] = str(opt["option_id"])

    async def get_all_tests(self):
        tests = await self.test_repo.get_all_tests()
        result = []
        for test in tests:
            questions = await self.question_repo.get_questions_by_test_id(test["_id"], include_deleted=False)
            await self._normalize_orders_and_options(questions)
            test["questions"] = questions
            test["num_questions"] = len(questions)
            result.append(test)
        return [convert_objectid_to_str(t) for t in result]

    async def get_test_detail(self, test_id: ObjectId):
        test = await self.test_repo.get_test_by_id(test_id)
        if not test or test.get("is_deleted"):
            return None
        questions = await self.question_repo.get_questions_by_test_id(test_id, include_deleted=False)
        await self._normalize_orders_and_options(questions)
        test["questions"] = questions
        return convert_objectid_to_str(test)

    async def create_test(self, test_data: dict, questions_data: List[dict], user_id: str):
        if await self.test_repo.collection.find_one({"test_code": test_data["test_code"], "is_deleted": False}):
            raise ValueError("Test code already exists")

        if test_data.get("severe_threshold", 0) <= 0:
            raise ValueError("severe_threshold must be greater than 0")

        if not questions_data:
            raise ValueError("At least one question is required")

        for q in questions_data:
            if len(q.get("options", [])) < 2:
                raise ValueError("Each question must have at least 2 options")

        test_data.update({
            "created_by": ObjectId(user_id),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_deleted": False
        })

        result = await self.test_repo.collection.insert_one(test_data)
        test_id = result.inserted_id

        await self._normalize_orders_and_options(questions_data)
        for q in questions_data:
            q.update({
                "test_id": test_id,
                "created_at": datetime.utcnow(),
                "is_deleted": False
            })
            await self.question_repo.collection.insert_one(q)

        return convert_objectid_to_str(await self.get_test_detail(test_id))

    async def update_test(self, test_id: ObjectId, update_data: dict):
        test = await self.test_repo.get_test_by_id(test_id)
        if not test or test.get("is_deleted"):
            raise ValueError("Test not found or has been deleted")

        # Cập nhật các field của test
        test_update = {k: v for k, v in update_data.items() if k != "questions" and v is not None}
        if test_update:
            test_update["updated_at"] = datetime.utcnow()
            await self.test_repo.collection.update_one({"_id": test_id}, {"$set": test_update})

        # XỬ LÝ QUESTIONS - QUAN TRỌNG NHẤT
        questions_payload = update_data.get("questions", [])
        if questions_payload:
            # TỰ ĐỘNG GÁN LẠI ORDER THEO THỨ TỰ MẢNG
            await self._normalize_orders_and_options(questions_payload)

            for q in questions_payload:
                qid = q.get("_id") or q.get("id")
                q_clean = {k: v for k, v in q.items() if k not in ["_id", "id"]}
                q_clean["test_id"] = test_id
                q_clean["updated_at"] = datetime.utcnow()

                if qid:
                    # UPDATE
                    result = await self.question_repo.collection.update_one(
                        {"_id": ObjectId(qid), "test_id": test_id},
                        {"$set": q_clean}
                    )
                    if result.matched_count == 0:
                        raise ValueError(f"Question {qid} not found")
                else:
                    # CREATE NEW
                    q_clean["created_at"] = datetime.utcnow()
                    q_clean["is_deleted"] = False
                    await self.question_repo.collection.insert_one(q_clean)

        return convert_objectid_to_str(await self.get_test_detail(test_id))

    async def soft_delete_test(self, test_id: ObjectId):
        test = await self.test_repo.get_test_by_id(test_id)
        if not test:
            raise ValueError("Test not found")
        await self.test_repo.collection.update_one(
            {"_id": test_id},
            {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
        )
        await self.question_repo.collection.update_many(
            {"test_id": test_id},
            {"$set": {"is_deleted": True, "deleted_at": datetime.utcnow()}}
        )
        return True


def get_admin_test_service(
    test_repo: TestRepository = Depends(get_test_repository),
    question_repo: TestQuestionRepository = Depends(get_question_repository)
):
    return AdminTestService(test_repo, question_repo)