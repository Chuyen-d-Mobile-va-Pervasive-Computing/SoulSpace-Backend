from bson import ObjectId
from typing import List, Dict
from app.repositories.test_repository import TestRepository
from app.repositories.user_test_result_repository import UserTestResultRepository
from app.schemas.user.test_schema import TestWithProgressResponseSchema
from fastapi import Depends

class TestNotFoundError(Exception): pass

class UserTestService:
    def __init__(self, test_repo: TestRepository, result_repo: UserTestResultRepository):
        self.test_repo = test_repo
        self.result_repo = result_repo

    async def get_all_tests_with_user_progress(self, user_id: ObjectId) -> List[TestWithProgressResponseSchema]:
        tests = await self.test_repo.get_all_tests()
        response_data = []

        for test in tests:
            test_id = test["_id"]
            num_questions = test.get("num_questions", 0)
            in_progress_result = await self.result_repo.find_in_progress_result(user_id, test_id)
            
            completion_percentage = 0.0
            if in_progress_result and num_questions > 0:
                answered_count = len(in_progress_result.get("answers", []))
                completion_percentage = (answered_count / num_questions) * 100
                if completion_percentage > 100: completion_percentage = 100.0

            response_data.append(
                TestWithProgressResponseSchema(
                    **test,
                    completion_percentage=round(completion_percentage, 2)
                )
            )
        return response_data

    async def get_questions_for_test(self, test_code: str) -> List[Dict]:
        test = await self.test_repo.get_test_by_code(test_code)
        if not test:
            raise TestNotFoundError(f"Test with code {test_code} not found")
        
        if test.get("is_deleted", False):
             raise TestNotFoundError(f"Test with code {test_code} is no longer available")

        questions = await self.test_repo.get_questions_by_test_id(test["_id"])
        return questions

# DI Helper
from app.repositories.test_repository import TestRepository
from app.core.database import get_db

def get_user_test_service(db=Depends(get_db)):
    test_repo = TestRepository(db)
    result_repo = UserTestResultRepository(db)
    return UserTestService(test_repo, result_repo)