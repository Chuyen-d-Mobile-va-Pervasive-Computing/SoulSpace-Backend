from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Optional, List
from app.models.test_questions_model import TestQuestion
from datetime import datetime

class TestQuestionRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection = database["test_questions"]

    async def get_questions_by_test_id(self, test_id: ObjectId, include_deleted: bool = False) -> List[dict]:
        query = {"test_id": ObjectId(test_id)}
        if not include_deleted:
            query["is_deleted"] = False
        questions = await self.collection.find(query).sort("question_order", 1).to_list(length=None)
        for q in questions:
            if "_id" in q:
                q["_id"] = str(q["_id"])
            # KHÔNG chuyển test_id thành string
            # Chuẩn hóa options
            if "options" in q:
                new_options = []
                for idx, opt in enumerate(q["options"]):
                    new_opt = {
                        "option_id": str(opt.get("_id", opt.get("option_id", ""))),
                        "option_text": opt.get("option_text", ""),
                        "score": opt.get("score_value", opt.get("score", 0)),
                        "option_order": opt.get("option_order", idx)
                    }
                    new_options.append(new_opt)
                q["options"] = new_options
        return questions

    async def get_question_by_id(self, question_id: ObjectId) -> Optional[dict]:
        q = await self.collection.find_one({"_id": ObjectId(question_id)})
        if q:
            if "_id" in q:
                q["_id"] = str(q["_id"])
            if "test_id" in q:
                q["test_id"] = str(q["test_id"])
        return q

    async def create_question(self, question_data: dict) -> str:
           # Tự động thêm trường is_deleted: False nếu chưa có
           question_data.setdefault("is_deleted", False)
           result = await self.collection.insert_one(question_data)
           return str(result.inserted_id)

    async def update_question(self, question_id: ObjectId, update_data: dict) -> bool:
        result = await self.collection.update_one({"_id": ObjectId(question_id)}, {"$set": update_data})
        return result.modified_count > 0

    async def soft_delete_question(self, question_id: ObjectId) -> bool:
        update_data = {"is_deleted": True, "deleted_at": datetime.utcnow()}
        result = await self.collection.update_one({"_id": ObjectId(question_id)}, {"$set": update_data})
        return result.modified_count > 0
