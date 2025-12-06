from app.repositories.test_question_repository import TestQuestionRepository
from bson import ObjectId
from typing import List

class UserTestQuestionService:
    def __init__(self, question_repo: TestQuestionRepository):
        self.question_repo = question_repo

    async def get_questions(self, test_id: ObjectId):
        return await self.question_repo.get_questions_by_test_id(test_id, include_deleted=False)
