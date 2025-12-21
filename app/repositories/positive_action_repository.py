from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any
from bson import ObjectId

class PositiveActionRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection = database["positive_actions"]

    async def get_all(self) -> List[Dict[str, Any]]:
        cursor = self.collection.find({})
        return await cursor.to_list(length=None)

    async def get_by_id(self, action_id: ObjectId | str) -> Dict[str, Any] | None:
        """
        Hỗ trợ cả ObjectId và string ID để tránh lỗi kiểu dữ liệu
        """
        if isinstance(action_id, str):
            if not ObjectId.is_valid(action_id):
                return None
            action_id = ObjectId(action_id)
        elif not isinstance(action_id, ObjectId):
            return None

        return await self.collection.find_one({"_id": action_id})