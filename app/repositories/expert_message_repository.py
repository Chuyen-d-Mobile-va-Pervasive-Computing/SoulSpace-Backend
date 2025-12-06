from bson import ObjectId
from datetime import datetime

class ExpertMessageRepository:
    def __init__(self, db):
        self.collection = db["expert_messages"]

    async def create(self, message_data: dict):
        result = await self.collection.insert_one(message_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def get(self, message_id: str):
        return await self.collection.find_one({"_id": ObjectId(message_id)})

    async def list_pending(self):
        return await self.collection.find({"status": "pending"}).sort("created_at", 1).to_list(length=100)

    async def list_by_expert(self, expert_id: str):
        return await self.collection.find({"expert_id": ObjectId(expert_id)}).sort("created_at", -1).to_list(length=100)

    async def list_by_user(self, user_id: str):
        return await self.collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1).to_list(length=100)

    async def update_status(self, message_id: str, status: str, expert_id: str = None):
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if expert_id:
            update_data["expert_id"] = ObjectId(expert_id)
        
        await self.collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": update_data}
        )
        return await self.get(message_id)

    async def add_response(self, message_id: str, response: str):
        await self.collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {
                "expert_response": response,
                "responded_at": datetime.utcnow(),
                "status": "resolved",
                "updated_at": datetime.utcnow()
            }}
        )
        return await self.get(message_id)
