from datetime import datetime
from app.repositories.anon_like_repository import AnonLikeRepository
from app.repositories.anon_post_repository import AnonPostRepository
from app.repositories.expert_article_repository import ExpertArticleRepository 
from bson import ObjectId

class AnonLikeService:
    def __init__(self, db):
        self.like_repo = AnonLikeRepository(db)
        self.post_repo = AnonPostRepository(db)
        self.article_repo = ExpertArticleRepository(db) # Init repo

    async def like_post(self, user_id: str, post_id: str):
        # 1. Thêm record vào bảng likes (bảng này dùng chung cho cả Post và Article)
        # post_id ở đây có thể là ID của Post hoặc Article
        new_like = await self.like_repo.like(post_id, user_id, datetime.utcnow())
        
        # 2. Thử tăng count trong AnonPost
        post_update = await self.post_repo.collection.update_one(
            {"_id": new_like["post_id"]},
            {"$inc": {"like_count": 1}}
        )
        
        # 3. Nếu không phải AnonPost (matched_count == 0), thử tăng count trong ExpertArticle
        if post_update.matched_count == 0:
            await self.article_repo.collection.update_one(
                {"_id": new_like["post_id"]},
                {"$inc": {"like_count": 1}}
            )
            
        return {"liked": True}

    async def unlike_post(self, user_id: str, post_id: str):
        # 1. Xóa like
        await self.like_repo.unlike(post_id, user_id)
        
        # 2. Thử giảm count trong AnonPost
        oid = ObjectId(post_id)
        post_update = await self.post_repo.collection.update_one(
            {"_id": oid},
            {"$inc": {"like_count": -1}}
        )
        
        # 3. Nếu không phải AnonPost, giảm count trong ExpertArticle
        if post_update.matched_count == 0:
            await self.article_repo.collection.update_one(
                {"_id": oid},
                {"$inc": {"like_count": -1}}
            )
            
        return {"liked": False}
        
    async def get_users_who_liked(self, post_id: str):
        """Lấy danh sách người đã like bài viết (cho cả Post và Article)"""
        return await self.like_repo.get_users_by_post_id(post_id)