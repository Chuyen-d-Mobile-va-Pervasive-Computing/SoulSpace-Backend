from app.models.notification_model import Notification
from bson import ObjectId

class NotificationRepository:
    def __init__(self, db):
        self.collection = db["notifications"]

    async def create(self, notification_data: dict):
        result = await self.collection.insert_one(notification_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def list_by_user(self, user_id: str):
        return await self.collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1).to_list(length=100)
    
    async def mark_as_read(self, notification_id: str):
        await self.collection.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"is_read": True}}
        )
