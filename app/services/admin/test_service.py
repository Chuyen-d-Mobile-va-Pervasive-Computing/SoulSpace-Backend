from bson import ObjectId
from typing import Dict
from datetime import datetime
from app.repositories.test_repository import TestRepository
from app.repositories.user_test_result_repository import UserTestResultRepository
from app.services.common.email_service import EmailService
from app.schemas.admin.test_schema import TestUpdatePayloadSchema, TestCreateSchema
from fastapi import Depends

class TestNotFoundError(Exception): pass
class TestAlreadyExistsError(Exception): pass

class AdminTestService:
    def __init__(self, test_repo: TestRepository, result_repo: UserTestResultRepository, email_service: EmailService):
        self.test_repo = test_repo
        self.result_repo = result_repo
        self.email_service = email_service

    async def create_test(self, payload: TestCreateSchema, admin_id: ObjectId) -> Dict:
        # 1. Check duplicate
        existing_test = await self.test_repo.get_test_by_code(payload.test_code)
        if existing_test:
            raise TestAlreadyExistsError(f"Test code '{payload.test_code}' already exists.")

        # 2. Insert Test Info
        test_data = payload.model_dump(exclude={"questions"})
        test_data.update({
            "num_questions": len(payload.questions),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": admin_id,
            "updated_by": admin_id,
            "is_deleted": False
        })
        
        result = await self.test_repo.tests_collection.insert_one(test_data)
        test_id = result.inserted_id
        test_data["_id"] = test_id

        # 3. Insert Questions 
        if payload.questions:
            await self._insert_formatted_questions(test_id, payload.questions)

        return test_data

    async def update_test_structure(self, test_code: str, payload: TestUpdatePayloadSchema, admin_id: ObjectId) -> Dict:
        test = await self.test_repo.get_test_by_code(test_code)
        if not test:
            raise TestNotFoundError(f"Test {test_code} not found")
        
        test_id = test["_id"]
        update_data = payload.model_dump(exclude={"questions"}, exclude_unset=True)
        
        if payload.questions is not None:
             update_data["num_questions"] = len(payload.questions)

        updated_test = await self.test_repo.update_test_info(test_id, update_data, admin_id)

        if payload.questions is not None:
            affected_emails = await self.result_repo.get_users_with_in_progress_test(test_id)
            
            # Xóa draft và câu hỏi cũ
            await self.result_repo.delete_in_progress_results_by_test_id(test_id)
            await self.test_repo.delete_questions_by_test_id(test_id)
            
            # Insert câu hỏi mới format chuẩn
            await self._insert_formatted_questions(test_id, payload.questions)

            # Gửi mail
            test_title = updated_test.get("title", test_code)
            for email in affected_emails:
                await self.email_service.send_test_update_notification(email, test_title)

        return updated_test

    async def _insert_formatted_questions(self, test_id: ObjectId, questions_payload: list):
        """Helper để format câu hỏi đúng chuẩn database cũ"""
        new_questions = []
        for q in questions_payload:
            formatted_options = []
            for opt in q.options:
                formatted_options.append({
                    "_id": ObjectId(), # ID lên đầu
                    "option_text": opt.option_text,
                    "score_value": opt.score_value
                })

            q_dict = {
                "test_id": test_id,
                "question_text": q.question_text,
                "question_order": q.question_order,
                "options": formatted_options,
                "is_deleted": False
            }
            new_questions.append(q_dict)
            
        if new_questions:
            await self.test_repo.insert_questions(new_questions)

    async def delete_test(self, test_code: str, user_id: ObjectId) -> None:
        success = await self.test_repo.soft_delete_test(test_code, user_id)
        if not success:
            raise TestNotFoundError(f"Test {test_code} not found")
        
# DI Helper
from app.repositories.test_repository import TestRepository
from app.core.database import get_db

def get_admin_test_service(db=Depends(get_db)) -> AdminTestService:
    test_repo = TestRepository(db)
    result_repo = UserTestResultRepository(db)
    email_service = EmailService()
    return AdminTestService(test_repo, result_repo, email_service)