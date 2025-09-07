from app.models.anon_post_model import AnonPost
from bson import ObjectId
from fastapi import HTTPException

class AnonPostRepository:
    def __init__(self, db):
        self.collection = db["anon_posts"]
        self.collection.create_index([("user_id", 1), ("created_at", -1), ("moderation_status", 1)])

    async def create(self, post: dict) -> dict:
        result = await self.collection.insert_one(post)
        post["_id"] = result.inserted_id
        return post

    async def get_by_id(self, post_id: str) -> dict:
        post = await self.collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post

    async def list(self, limit: int = 20) -> list:
        cursor = self.collection.find({"moderation_status": "Approved"}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_status(self, post_id: str, status: str, reason: str = None) -> dict:
        result = await self.collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"moderation_status": status, "flagged_reason": reason}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Post not found")
        return await self.get_by_id(post_id)