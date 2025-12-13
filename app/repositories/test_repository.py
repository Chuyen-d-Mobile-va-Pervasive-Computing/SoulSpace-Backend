from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Dict, Any
from datetime import datetime

class TestRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.tests_collection = database["tests"]
        self.questions_collection = database["test_questions"]

    async def get_all_tests(self) -> List[Dict[str, Any]]:
        cursor = self.tests_collection.find({"is_deleted": False})
        return await cursor.to_list(length=None) 

    async def get_test_by_code(self, test_code: str) -> Dict[str, Any] | None:
        return await self.tests_collection.find_one({"test_code": test_code})

    async def get_by_id(self, test_id: ObjectId) -> Dict | None:
        return await self.tests_collection.find_one({"_id": test_id})

    async def get_questions_by_test_id(self, test_id: ObjectId) -> List[Dict[str, Any]]:
        cursor = self.questions_collection.find({"test_id": test_id}).sort("question_order", 1)
        return await cursor.to_list(length=None)

    async def update_test_info(self, test_id: ObjectId, update_data: Dict, user_id: ObjectId) -> Dict | None:
        update_data["updated_at"] = datetime.utcnow()
        update_data["updated_by"] = user_id
        
        result = await self.tests_collection.find_one_and_update(
            {"_id": test_id},
            {"$set": update_data},
            return_document=True
        )
        return result

    async def delete_questions_by_test_id(self, test_id: ObjectId) -> int:
        result = await self.questions_collection.delete_many({"test_id": test_id})
        return result.deleted_count

    async def insert_questions(self, questions_data: List[Dict]) -> None:
        if questions_data:
            await self.questions_collection.insert_many(questions_data)

    async def soft_delete_test(self, test_code: str, user_id: ObjectId) -> bool:
        result = await self.tests_collection.update_one(
            {"test_code": test_code},
            {"$set": {
                "is_deleted": True,
                "updated_at": datetime.utcnow(),
                "updated_by": user_id
            }}
        )
        return result.modified_count > 0