from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Dict, Any

class TestRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.tests_collection = database["tests"]
        self.questions_collection = database["test_questions"]

    async def get_all_tests(self) -> List[Dict[str, Any]]:
        cursor = self.tests_collection.find({})
        return await cursor.to_list(length=None) 

    async def get_test_by_code(self, test_code: str) -> Dict[str, Any] | None:
        return await self.tests_collection.find_one({"test_code": test_code})

    async def get_questions_by_test_id(self, test_id: ObjectId) -> List[Dict[str, Any]]:
        cursor = self.questions_collection.find({"test_id": test_id}).sort("question_order", 1)
        return await cursor.to_list(length=None)