from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Dict, Any
from pymongo import ReturnDocument

class UserTestResultRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection = database["user_test_results"]

    async def get_by_id(self, result_id: Any) -> Dict | None:
        return await self.collection.find_one({"_id": ObjectId(result_id)})

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

    async def create_draft(self, draft_data: Dict) -> Dict:
        result = await self.collection.insert_one(draft_data)
        draft_data["_id"] = result.inserted_id
        return draft_data

    async def find_and_finalize_result(self, result_id: Any, final_data: Dict) -> Dict | None:
        valid_id = ObjectId(result_id)

        updated_document = await self.collection.find_one_and_update(
            {"_id": valid_id},
            {"$set": final_data},
            return_document=ReturnDocument.AFTER
        )
        return updated_document

    async def create_result(self, result_data: Dict) -> Dict:
        result = await self.collection.insert_one(result_data)
        result_data["_id"] = result.inserted_id
        return result_data
