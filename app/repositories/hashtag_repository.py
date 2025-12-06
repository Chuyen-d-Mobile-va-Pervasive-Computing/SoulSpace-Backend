from bson import ObjectId
from datetime import datetime

class HashtagRepository:
    def __init__(self, db):
        self.collection = db["hashtags"]

    async def create(self, hashtag_data: dict):
        result = await self.collection.insert_one(hashtag_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def find_by_name(self, name: str):
        return await self.collection.find_one({"name": name})

    async def increment_usage(self, name: str):
        return await self.collection.update_one(
            {"name": name},
            {
                "$inc": {"usage_count": 1},
                "$set": {"last_used_at": datetime.utcnow()}
            }
        )

    async def get_or_create(self, name: str):
        existing = await self.find_by_name(name)
        if existing:
            await self.increment_usage(name)
            return existing
        
        hashtag_data = {
            "name": name,
            "usage_count": 1,
            "created_at": datetime.utcnow(),
            "last_used_at": datetime.utcnow()
        }
        return await self.create(hashtag_data)

    async def list_popular(self, limit: int = 20):
        return await self.collection.find().sort("usage_count", -1).limit(limit).to_list(length=limit)

    async def search(self, query: str, limit: int = 10):
        return await self.collection.find(
            {"name": {"$regex": query, "$options": "i"}}
        ).limit(limit).to_list(length=limit)
