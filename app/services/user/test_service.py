import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends

from app.repositories.test_repository import TestRepository
from app.repositories.user_test_result_repository import UserTestResultRepository
from bson import ObjectId
from typing import List
from app.core.database import get_db
from app.utils.pyobjectid import PyObjectId 
from app.core.dependencies import get_test_repository, get_user_test_result_repository

class TestNotFoundError(Exception):
    pass

class TestDataIntegrityError(Exception):
    pass

class DatabaseOperationError(Exception):
    pass


class TestService:
    def __init__(self, test_repo: TestRepository, user_test_result_repo: UserTestResultRepository):
        self.test_repo = test_repo
        self.user_test_result_repo = user_test_result_repo

    async def get_all_tests(self):
        try:
            tests = await self.test_repo.get_all_tests()
            for test in tests:
                # Always add num_questions for schema validation
                questions = test.get("questions")
                if questions is not None:
                    test["num_questions"] = len(questions)
                else:
                    test["num_questions"] = 0
            return tests
        except Exception as e:
            raise DatabaseOperationError(f"A database error occurred: {e}")

    async def get_questions_for_test(self, test_code: str):
        try:
            test_document = await self.test_repo.get_test_by_code(test_code)

            if not test_document:
                raise TestNotFoundError(f"Test with code '{test_code}' could not be found.")

            test_id = test_document["_id"]
            questions = await self.test_repo.get_questions_by_test_id(test_id)

            if not questions:
                raise TestDataIntegrityError(f"Data integrity issue: Test '{test_code}' (ID: {test_id}) exists but has no questions.")

            return questions

        except (TestNotFoundError, TestDataIntegrityError) as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred: {e}")

    async def get_all_tests_with_user_progress(self, user_id: PyObjectId):
        try:
            # 1. Lấy tất cả các bài test có sẵn
            all_tests = await self.test_repo.get_all_tests()
            if not all_tests:
                return []

            # 2. Lấy tất cả kết quả của người dùng hiện tại
            user_results = await self.user_test_result_repo.get_all_results_by_user_id(user_id)

            # 3. Tạo một map để tra cứu kết quả theo test_id cho hiệu quả
            # Key: test_id (dạng string), Value: document kết quả
            user_results_map = {str(result['test_id']): result for result in user_results}

            # 4. Lặp qua từng bài test và tính toán % hoàn thành
            tests_with_progress = []
            for test in all_tests:
                test_id_str = str(test['_id'])
                completion_percentage = 0.0
                
                user_result = user_results_map.get(test_id_str)

                if user_result:
                    if user_result.get('status') == 'completed':
                        completion_percentage = 100.0
                    elif user_result.get('status') == 'in-progress':
                        num_answered = len(user_result.get('answers', []))
                        total_questions = test.get('num_questions', 1) # Tránh chia cho 0
                        if total_questions > 0:
                            completion_percentage = (num_answered / total_questions) * 100
                
                # Tạo một bản sao và thêm trường mới
                test_data = test.copy()
                test_data['completion_percentage'] = round(completion_percentage, 2)
                tests_with_progress.append(test_data)
            
            return tests_with_progress

        except Exception as e:
            raise DatabaseOperationError(f"A database error occurred while fetching tests with progress: {e}")

class UserTestService:
    def __init__(self, test_repo: TestRepository, result_repo: UserTestResultRepository):
        self.test_repo = test_repo
        self.result_repo = result_repo

    async def get_all_tests(self):
        # Chỉ trả về test chưa bị xóa
        tests = await self.test_repo.collection.find({"is_deleted": False}).to_list(length=None)
        # Đếm số lượng câu hỏi cho từng test
        from app.repositories.test_question_repository import TestQuestionRepository
        question_repo = TestQuestionRepository(self.test_repo.collection.database)
        for test in tests:
            test_id = test.get("_id")
            if test_id:
                num_questions = await question_repo.collection.count_documents({"test_id": test_id, "is_deleted": False})
                test["num_questions"] = num_questions
            else:
                test["num_questions"] = 0
        return tests

    def _convert_objectid_to_str(self, obj):
        # Recursively convert all ObjectId in dict/list to string
        from bson import ObjectId
        if isinstance(obj, dict):
            return {k: self._convert_objectid_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_objectid_to_str(i) for i in obj]
        elif isinstance(obj, ObjectId):
            return str(obj)
        else:
            return obj

    async def get_test_questions(self, test_code: str):
        test = await self.test_repo.get_test_by_code(test_code)
        if not test or test.get("is_deleted"):
            return []
        from app.repositories.test_question_repository import TestQuestionRepository
        question_repo = TestQuestionRepository(self.test_repo.collection.database)
        questions = await question_repo.get_questions_by_test_id(test["_id"], include_deleted=False)
        return self._convert_objectid_to_str(questions)


def get_test_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TestRepository:
    return TestRepository(database=db)

def get_user_test_service(
    test_repo: TestRepository = Depends(get_test_repository),
    user_test_result_repo: UserTestResultRepository = Depends(get_user_test_result_repository)
) -> UserTestService:
    return UserTestService(test_repo=test_repo, result_repo=user_test_result_repo)

def get_test_service(
    test_repo: TestRepository = Depends(get_test_repository),
    user_test_result_repo: UserTestResultRepository = Depends(get_user_test_result_repository)
) -> TestService:
    return TestService(test_repo=test_repo, user_test_result_repo=user_test_result_repo)