from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Dict, Any
from pymongo import ReturnDocument,  DESCENDING

class UserTestResultRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection = database["user_test_results"]
        self.tests_collection = database["tests"]

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
    
    async def get_all_results_by_user_id(self, user_id: ObjectId) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"user_id": user_id})
        return await cursor.to_list(length=None)

    async def get_users_with_in_progress_test(self, test_id: ObjectId) -> List[str]:
        """Get emails of users who have an in-progress draft for this test."""
        pipeline = [
            {"$match": {
                "test_id": test_id,
                "status": "in-progress"
            }},
            {"$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user_info"
            }},
            {"$unwind": "$user_info"},
            {"$project": {"email": "$user_info.email"}}
        ]
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        return [r["email"] for r in results if "email" in r]

    async def delete_in_progress_results_by_test_id(self, test_id: ObjectId) -> int:
        result = await self.collection.delete_many({
            "test_id": test_id,
            "status": "in-progress"
        })
        return result.deleted_count

    async def get_latest_completed_results_by_user(self, user_id: ObjectId) -> List[Dict[str, Any]]:
        pipeline = [
            {"$match": {"user_id": user_id, "status": "completed"}},
            {"$sort": {"completed_at": DESCENDING}},
            {"$group": {
                "_id": "$test_id",
                "latest_result": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest_result"}},
            {"$lookup": {
                "from": "tests",
                "localField": "test_id",
                "foreignField": "_id",
                "as": "test_info"
            }},
            {"$unwind": "$test_info"},
            {"$addFields": {
                "max_score": {"$multiply": ["$test_info.num_questions", 3]}
            }},
            {"$project": {
                "result_id": "$_id",
                "test_id": "$test_id",
                "test_code": "$test_info.test_code",
                "test_name": "$test_info.title",
                "completed_at": "$completed_at",
                "severity_level": "$severity_level",
                "score_ratio": {
                    "$concat": [
                        {"$toString": "$total_score"},
                        "/",
                        {"$toString": "$max_score"}
                    ]
                },
                "_id": 0
            }}
        ]
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)