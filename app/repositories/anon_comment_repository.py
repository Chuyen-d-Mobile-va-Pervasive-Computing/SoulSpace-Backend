from app.models.anon_comment_model import AnonComment
from bson import ObjectId
from fastapi import HTTPException

class AnonCommentRepository:
    def __init__(self, db):
        self.collection = db["anon_comments"]
        self.collection.create_index([("post_id", 1), ("created_at", -1)])

    async def create(self, comment: dict) -> dict:
        result = await self.collection.insert_one(comment)
        comment["_id"] = result.inserted_id
        return comment

    async def get_by_id(self, comment_id: str) -> dict:
        comment = await self.collection.find_one({"_id": ObjectId(comment_id)})
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        return comment

    async def list_by_post(self, post_id: str, limit: int = 50) -> list:
        cursor = self.collection.find({"post_id": ObjectId(post_id), "moderation_status": "Approved"}) \
            .sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_status(self, comment_id: str, status: str) -> dict:
        result = await self.collection.update_one(
            {"_id": ObjectId(comment_id)},
            {"$set": {"moderation_status": status}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Comment not found")
        return await self.get_by_id(comment_id)
    
    async def delete(self, comment_id: str) -> dict:
        comment = await self.collection.find_one({"_id": ObjectId(comment_id)})
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        await self.collection.delete_one({"_id": ObjectId(comment_id)})
        return comment