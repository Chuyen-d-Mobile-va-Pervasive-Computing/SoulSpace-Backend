from app.repositories.test_question_repository import TestQuestionRepository
from bson import ObjectId
from typing import List, Optional
from datetime import datetime

class AdminTestQuestionService:
    def __init__(self, question_repo: TestQuestionRepository):
        self.question_repo = question_repo

    async def get_questions(self, test_id: ObjectId):
        return await self.question_repo.get_questions_by_test_id(test_id, include_deleted=False)

    async def create_question(self, question_data: dict):
        question_data["created_at"] = datetime.utcnow()
        return await self.question_repo.create_question(question_data)

    async def update_question(self, question_id: ObjectId, update_data: dict):
        update_data["updated_at"] = datetime.utcnow()
        return await self.question_repo.update_question(question_id, update_data)

    async def soft_delete_question(self, question_id: ObjectId):
        return await self.question_repo.soft_delete_question(question_id)
