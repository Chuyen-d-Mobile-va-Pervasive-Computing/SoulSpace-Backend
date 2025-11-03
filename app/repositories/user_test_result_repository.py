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
    

    async def get_latest_completed_results_by_user(self, user_id: ObjectId) -> List[Dict[str, Any]]:

        pipeline = [
            # 1. Lọc các kết quả của user_id và đã 'completed'
            {
                "$match": {
                    "user_id": user_id,
                    "status": "completed"
                }
            },
            # 2. Sắp xếp theo ngày hoàn thành, mới nhất lên đầu
            {
                "$sort": {
                    "completed_at": DESCENDING
                }
            },
            # 3. Gom nhóm theo test_id, chỉ lấy bản ghi đầu tiên (mới nhất)
            {
                "$group": {
                    "_id": "$test_id",
                    "latest_result": {"$first": "$$ROOT"}
                }
            },
            # 4. "Mở" document latest_result ra
            {
                "$replaceRoot": {
                    "newRoot": "$latest_result"
                }
            },
            # 5. Join với collection 'tests' để lấy thông tin test
            {
                "$lookup": {
                    "from": "tests",
                    "localField": "test_id",
                    "foreignField": "_id",
                    "as": "test_info"
                }
            },
            # 6. "Mở" mảng test_info ra (chỉ có 1 phần tử)
            {
                "$unwind": "$test_info"
            },
            # 7. Tính điểm tối đa (num_questions * 3, giả sử mỗi câu max 3 điểm)
            # Đây là một giả định, bạn có thể cần một cách tính chính xác hơn
            {
                "$addFields": {
                    "max_score": {"$multiply": ["$test_info.num_questions", 3]}
                }
            },
            # 8. Định dạng lại output cuối cùng
            {
                "$project": {
                    "result_id": "$_id",
                    "test_id": "$test_id",
                    "test_code": "$test_info.test_code",
                    "test_name": "$test_info.test_name",
                    "completed_at": "$completed_at",
                    "severity_level": "$severity_level",
                    "score_ratio": {
                        "$concat": [
                            {"$toString": "$total_score"},
                            "/",
                            {"$toString": "$max_score"}
                        ]
                    },
                    "_id": 0 # Bỏ trường _id mặc định của aggregation
                }
            }
        ]
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)