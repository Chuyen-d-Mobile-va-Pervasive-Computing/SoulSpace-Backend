from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_db
from app.repositories.test_repository import TestRepository
from app.repositories.test_question_repository import TestQuestionRepository
from app.repositories.test_repository import TestRepository
from app.repositories.test_question_repository import TestQuestionRepository
from bson import ObjectId
from typing import List, Optional
from datetime import datetime

class AdminTestService:
    def __init__(self, test_repo: TestRepository, question_repo: TestQuestionRepository):
        self.test_repo = test_repo
        self.question_repo = question_repo

    async def get_all_tests(self):
        from app.utils.convert import convert_objectid_to_str
        tests = await self.test_repo.get_all_tests()
        for test in tests:
            try:
                questions = await self.question_repo.get_questions_by_test_id(test["_id"], include_deleted=False)
                test["questions"] = questions
                test["num_questions"] = len(questions)
            except Exception:
                # Nếu không truy vấn được questions, vẫn đảm bảo có num_questions
                test["num_questions"] = 0
        return convert_objectid_to_str(tests)

    async def get_test_detail(self, test_id: ObjectId):
        from app.utils.convert import convert_objectid_to_str
        test = await self.test_repo.get_test_by_id(test_id)
        if not test:
            return None
        from bson import ObjectId as BsonObjectId
        # Đảm bảo test_id truyền vào truy vấn là ObjectId
        questions = await self.question_repo.get_questions_by_test_id(BsonObjectId(test["_id"]), include_deleted=False)
        test["questions"] = questions
        return convert_objectid_to_str(test)

    async def create_test(self, test_data: dict, questions_data: List[dict], user_id: str):
        # Validate unique test_code, title, severe_threshold > 0, min 1 question, mỗi question min 2 options
        if not await self.test_repo.is_test_code_unique(test_data["test_code"]):
            raise ValueError("Test code must be unique.")
        if not test_data.get("title"):
            raise ValueError("Title is required.")
        if test_data.get("severe_threshold", 0) <= 0:
            raise ValueError("Severe threshold must be > 0.")
        if not questions_data or len(questions_data) < 1:
            raise ValueError("At least 1 question is required.")
        for q in questions_data:
            if not q.get("options") or len(q["options"]) < 2:
                raise ValueError("Each question must have at least 2 options.")
        test_data["created_by"] = user_id
        test_data["created_at"] = datetime.utcnow()
        test_id = await self.test_repo.create_test(test_data)
        from bson import ObjectId as BsonObjectId
        for q in questions_data:
            q["test_id"] = ObjectId(test_id)
            q["created_at"] = datetime.utcnow()
            # Sinh option_id cho mỗi option nếu chưa có
            if "options" in q:
                for opt in q["options"]:
                    if not opt.get("option_id"):
                        opt["option_id"] = str(BsonObjectId())
            await self.question_repo.create_question(q)
        return test_id

    async def update_test(self, test_id: ObjectId, update_data: dict):
        # Cập nhật trường của test
        test_fields = update_data.get("test", {})
        test_fields["updated_at"] = datetime.utcnow()
        await self.test_repo.update_test(test_id, test_fields)

        # Cập nhật từng câu hỏi
        questions = update_data.get("questions", [])
        for q in questions:
            question_id = q.get("_id")
            if question_id:
                q_fields = {k: v for k, v in q.items() if k != "_id"}
                q_fields["updated_at"] = datetime.utcnow()
                await self.question_repo.update_question(ObjectId(question_id), q_fields)
                # Nếu cần cập nhật options, bổ sung logic tại đây
        return True

    async def soft_delete_test(self, test_id: ObjectId):
        # Xóa mềm test
        result = await self.test_repo.soft_delete_test(test_id)
        # Xóa mềm tất cả question liên quan
        questions = await self.question_repo.get_questions_by_test_id(test_id, include_deleted=True)
        for q in questions:
            await self.question_repo.soft_delete_question(q["_id"])
        return result


# Provider functions đặt sau class AdminTestService
def get_test_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TestRepository:
    return TestRepository(database=db)

def get_question_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TestQuestionRepository:
    return TestQuestionRepository(database=db)

def get_admin_test_service(
    test_repo: TestRepository = Depends(get_test_repository),
    question_repo: TestQuestionRepository = Depends(get_question_repository)
) -> 'AdminTestService':
    return AdminTestService(test_repo=test_repo, question_repo=question_repo)
