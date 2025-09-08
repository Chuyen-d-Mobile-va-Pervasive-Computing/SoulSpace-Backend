from datetime import datetime
from app.repositories.anon_like_repository import AnonLikeRepository
from app.repositories.anon_post_repository import AnonPostRepository
from bson import ObjectId

class AnonLikeService:
    def __init__(self, db):
        self.like_repo = AnonLikeRepository(db)
        self.post_repo = AnonPostRepository(db)

    async def like_post(self, user_id: str, post_id: str):
        # thêm like
        new_like = await self.like_repo.like(post_id, user_id, datetime.utcnow())
        # tăng like_count trong post
        await self.post_repo.collection.update_one(
            {"_id": new_like["post_id"]},
            {"$inc": {"like_count": 1}}
        )
        return {"liked": True}

    async def unlike_post(self, user_id: str, post_id: str):
        # xóa like
        await self.like_repo.unlike(post_id, user_id)
        # giảm like_count trong post
        await self.post_repo.collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"like_count": -1}}
        )
        return {"liked": False}