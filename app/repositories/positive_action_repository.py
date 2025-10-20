from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any
from bson import ObjectId

class PositiveActionRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection = database["positive_actions"]

    async def get_all(self) -> List[Dict[str, Any]]:
        cursor = self.collection.find({})
        return await cursor.to_list(length=None)

    async def get_by_id(self, action_id: ObjectId) -> Dict[str, Any] | None:
        return await self.collection.find_one({"_id": action_id})