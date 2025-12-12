# app/repositories/user_test_result_repository.py
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Optional, List, Dict, Any
from pymongo import ReturnDocument
from app.models.user_test_results_model import UserTestResult
class UserTestResultRepository:
    async def get_by_id(self, result_id: ObjectId) -> dict | None:
        return await self.get_result_by_id(result_id)
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection = database["user_test_results"]

    async def get_results_by_user_id(self, user_id: ObjectId) -> List[dict]:
        return await self.collection.find({"user_id": ObjectId(user_id)}).to_list(length=None)

    async def get_result_by_id(self, result_id: ObjectId) -> Optional[dict]:
        return await self.collection.find_one({"_id": ObjectId(result_id)})

    async def create_result(self, result_data: dict) -> ObjectId:
        result = await self.collection.insert_one(result_data)
        return result.inserted_id

    async def update_result(self, result_id: ObjectId, update_data: dict) -> bool:
        result = await self.collection.update_one({"_id": ObjectId(result_id)}, {"$set": update_data})
        return result.modified_count > 0

    async def get_result_by_user_and_test(self, user_id: ObjectId, test_id: ObjectId) -> Optional[dict]:
        return await self.collection.find_one({"user_id": ObjectId(user_id), "test_id": ObjectId(test_id)})

    async def find_in_progress_result(self, user_id: ObjectId, test_id: ObjectId) -> Dict | None:
        return await self.collection.find_one({
            "user_id": user_id,
            "test_id": test_id,
            "status": "in-progress"
        })

    async def update_answers(self, result_id: ObjectId, updated_answers: List[Dict]) -> None:
        await self.collection.update_one(
            {"_id": result_id},
            {"$set": {"answers": updated_answers}}
        )