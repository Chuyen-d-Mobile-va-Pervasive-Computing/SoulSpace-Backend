from app.models.anon_comment_model import AnonComment
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Optional

class AnonCommentRepository:
    def __init__(self, db):
        self.collection = db["anon_comments"]
        self.users_collection = db["users"]
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

    async def _enrich_comment(self, comment: dict, current_user_id: Optional[str] = None) -> dict:
        comment_user_id = comment.get("user_id")
        is_anonymous = comment.get("is_anonymous", False)  # Lấy từ DB

        # Logic check owner
        is_owner = (
            current_user_id is not None and
            str(comment_user_id) == current_user_id
        ) if comment_user_id else False

        if comment_user_id:
            user = await self.users_collection.find_one(
                {"_id": ObjectId(comment_user_id)},
                {"username": 1, "role": 1, "avatar_url": 1}
            )

            if user:
                # Nếu ẩn danh và không phải owner đang xem → ẩn info
                if is_anonymous and not is_owner:
                    comment["username"] = "Anonymous"
                    comment["avatar_url"] = None
                    comment["user_id"] = None
                else:
                    # Hiển thị thật nếu không ẩn danh HOẶC là owner
                    comment["username"] = user.get("username", "Anonymous")
                    comment["avatar_url"] = user.get("avatar_url")
                    comment["user_id"] = str(comment_user_id)

                comment["role"] = user.get("role", "user")
            else:
                comment["username"] = "Anonymous"
                comment["role"] = "user"
                comment["avatar_url"] = None
                comment["user_id"] = None
        else:
            comment["username"] = "Anonymous"
            comment["role"] = "user"
            comment["avatar_url"] = None
            comment["user_id"] = None

        comment["is_owner"] = is_owner

        comment["is_anonymous"] = is_anonymous

        return comment

    async def list_by_post(self, post_id: str, current_user_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        cursor = self.collection.find({
            "post_id": ObjectId(post_id),
            "moderation_status": "Approved"
        }).sort("created_at", -1).limit(limit)

        comments = await cursor.to_list(length=limit)

        # Enrich each comment
        enriched_comments = []
        for comment in comments:
            enriched = await self._enrich_comment(comment, current_user_id)
            enriched_comments.append(enriched)

        return enriched_comments

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