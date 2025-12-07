from app.models.anon_post_model import AnonPost
from bson import ObjectId
from fastapi import HTTPException
from typing import Optional

class AnonPostRepository:
    def __init__(self, db):
        self.db = db
        self.collection = db["anon_posts"]
        self.users_collection = db["users"]
        self.likes_collection = db["anon_likes"]
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

    async def get_by_id_with_author(self, post_id: str, current_user_id: Optional[str] = None) -> dict:
        """Lấy post với thông tin author và check like/owner status."""
        post = await self.get_by_id(post_id)
        return await self._enrich_post(post, current_user_id)

    async def _enrich_post(self, post: dict, current_user_id: Optional[str] = None) -> dict:
        """Bổ sung author_name, is_liked, is_owner cho post."""
        post_user_id = post.get("user_id")
        
        # Xác định author_name
        if post.get("is_anonymous", True):
            post["author_name"] = "Ẩn danh"
            post["user_id"] = None  # Ẩn user_id khi ẩn danh
        else:
            # Lấy username từ users collection
            user = await self.users_collection.find_one(
                {"_id": ObjectId(post_user_id) if isinstance(post_user_id, str) else post_user_id},
                {"username": 1}
            )
            post["author_name"] = user.get("username", "Người dùng") if user else "Người dùng"
            post["user_id"] = str(post_user_id)
        
        # Check is_owner và is_liked
        if current_user_id:
            current_user_oid = ObjectId(current_user_id) if isinstance(current_user_id, str) else current_user_id
            post_user_oid = ObjectId(post_user_id) if isinstance(post_user_id, str) else post_user_id
            
            # Check owner
            post["is_owner"] = str(current_user_oid) == str(post_user_oid)
            
            # Nếu là owner, hiển thị user_id
            if post["is_owner"]:
                post["user_id"] = str(post_user_id)
            
            # Check liked
            like = await self.likes_collection.find_one({
                "post_id": post["_id"],
                "user_id": current_user_oid
            })
            post["is_liked"] = like is not None
        else:
            post["is_owner"] = False
            post["is_liked"] = False
        
        return post

    async def list(self, limit: int = 20, current_user_id: Optional[str] = None) -> list:
        """Lấy danh sách posts đã duyệt với thông tin author."""
        cursor = self.collection.find({"moderation_status": "Approved"}).sort("created_at", -1).limit(limit)
        posts = await cursor.to_list(length=limit)
        
        # Enrich mỗi post với author info
        enriched_posts = []
        for post in posts:
            enriched_post = await self._enrich_post(post, current_user_id)
            enriched_posts.append(enriched_post)
        
        return enriched_posts

    async def list_by_user(self, user_id: str, limit: int = 50) -> list:
        """Lấy tất cả posts của một user (bao gồm cả pending)."""
        cursor = self.collection.find({
            "user_id": ObjectId(user_id)
        }).sort("created_at", -1).limit(limit)
        posts = await cursor.to_list(length=limit)
        
        enriched_posts = []
        for post in posts:
            enriched_post = await self._enrich_post(post, user_id)
            enriched_posts.append(enriched_post)
        
        return enriched_posts

    async def update_status(self, post_id: str, status: str, reason: str = None) -> dict:
        result = await self.collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"moderation_status": status, "flagged_reason": reason}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Post not found")
        return await self.get_by_id(post_id)
    
    async def increment_comment_count(self, post_id: str):
        await self.collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"comment_count": 1}}
        )

    async def decrement_comment_count(self, post_id: str):
        await self.collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"comment_count": -1}}
        )

    async def delete(self, post_id: str) -> dict:
        post = await self.collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        await self.collection.delete_one({"_id": ObjectId(post_id)})
        return post
    
    async def get(self, post_id: str) -> dict:
        """Alias for get_by_id - compatibility."""
        return await self.get_by_id(post_id)