from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Dict, Any
from app.models.user_tree_model import UserTree

class UserTreeRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection = database["user_tree"]

    async def get_by_user_id(self, user_id: ObjectId) -> Dict[str, Any] | None:
        return await self.collection.find_one({"user_id": user_id})

    async def create(self, user_tree: UserTree) -> Dict[str, Any]:
        await self.collection.create_index("user_id", unique=True)
        
        document_to_insert = {
            "_id": user_tree.id,
            "user_id": user_tree.user_id,
            "total_xp": user_tree.total_xp,
            "streak_days": user_tree.streak_days,
            "last_watered_at": user_tree.last_watered_at,
            "actions": [action.model_dump(mode='python') for action in user_tree.actions]
        }
        
        result = await self.collection.insert_one(document_to_insert)
        created_tree = await self.collection.find_one({"_id": result.inserted_id})
        return created_tree

    async def update(self, user_id: ObjectId, update_data: Dict[str, Any]) -> bool:
        result = await self.collection.update_one(
            {"user_id": user_id},
            update_data
        )
        return result.modified_count > 0