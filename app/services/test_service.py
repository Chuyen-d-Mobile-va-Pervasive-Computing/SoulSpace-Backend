import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends

from app.repositories.test_repository import TestRepository
from app.core.database import get_db

class TestNotFoundError(Exception):
    pass

class TestDataIntegrityError(Exception):
    pass

class DatabaseOperationError(Exception):
    pass


class TestService:
    def __init__(self, test_repo: TestRepository):
        self.test_repo = test_repo

    async def get_all_tests(self):
        try:
            tests = await self.test_repo.get_all_tests()
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



def get_test_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TestRepository:
    return TestRepository(database=db)

def get_test_service(
    test_repo: TestRepository = Depends(get_test_repository)
) -> TestService:
    return TestService(test_repo=test_repo)