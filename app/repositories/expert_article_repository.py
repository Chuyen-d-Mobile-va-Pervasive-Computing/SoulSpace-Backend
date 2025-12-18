from bson import ObjectId
from typing import Optional
from fastapi import HTTPException

class ExpertArticleRepository:
    def __init__(self, db):
        self.db = db
        self.collection = db["expert_articles"]
        self.expert_profiles = db["expert_profiles"]
        self.likes_collection = db["anon_likes"] # Dùng chung bảng like với user post

    async def create(self, article_data: dict):
        result = await self.collection.insert_one(article_data)
        article_data["_id"] = result.inserted_id
        return await self._enrich_article(article_data)

    async def _enrich_article(self, article: dict, current_user_id: Optional[str] = None) -> dict:
        """Bổ sung thông tin author và tương tác"""
        
        # 1. Lấy thông tin Expert Author
        expert = await self.expert_profiles.find_one(
            {"_id": article["expert_id"]},
            {"full_name": 1, "avatar_url": 1, "user_id": 1}
        )
        
        if expert:
            # Map cho ExpertArticleResponse
            article["expert_name"] = expert.get("full_name")
            article["expert_avatar"] = expert.get("avatar_url")
            
            # Map cho FeedItemResponse (chung)
            article["author_name"] = expert.get("full_name")
            article["author_avatar"] = expert.get("avatar_url")
            article["author_id"] = str(article["expert_id"])
            article["author_role"] = "expert"
            
            article["is_owner"] = (str(expert.get("user_id")) == str(current_user_id)) if current_user_id else False
        else:
            article["expert_name"] = "Unknown"
            article["author_name"] = "Unknown"
            article["is_owner"] = False

        # 2. Check Like Status
        if current_user_id:
            like = await self.likes_collection.find_one({
                "post_id": article["_id"],
                "user_id": ObjectId(current_user_id)
            })
            article["is_liked"] = like is not None
        else:
            article["is_liked"] = False
            
        return article

    async def list_by_status(self, status: str, limit: int = 100):
        """Lấy danh sách theo status (Dùng cho Admin/Expert quản lý)"""
        cursor = self.collection.find({"status": status}).sort("created_at", -1).limit(limit)
        articles = await cursor.to_list(length=limit)
        return [await self._enrich_article(a) for a in articles]

    async def list_all(self, limit: int = 100):
        """Lấy tất cả bài viết không phân biệt status (Dùng cho Admin)"""
        cursor = self.collection.find({}).sort("created_at", -1).limit(limit)
        articles = await cursor.to_list(length=limit)
        return [await self._enrich_article(a) for a in articles]
    
    async def get_by_id(self, article_id: str, current_user_id: Optional[str] = None):
        try:
            oid = ObjectId(article_id)
        except:
            return None
        
        article = await self.collection.find_one({"_id": oid})
        if article:
            return await self._enrich_article(article, current_user_id)
        return None

    async def list_by_expert(self, expert_id: str, current_user_id: Optional[str] = None):
        filters = [{"expert_id": expert_id}]
        
        if ObjectId.is_valid(expert_id):
            filters.append({"expert_id": ObjectId(expert_id)})
            
        query = {"$or": filters}
        
        try:
            cursor = self.collection.find(query).sort("created_at", -1)
            articles = await cursor.to_list(length=100)
            return [await self._enrich_article(a, current_user_id) for a in articles]
        except Exception as e:
            print(f"Error listing expert articles: {e}")
            return []

    async def list_approved_feed(self, limit: int = 50, current_user_id: Optional[str] = None):
        """Lấy danh sách bài PR đã duyệt"""
        cursor = self.collection.find({"status": "approved"}).sort("approved_at", -1).limit(limit)
        articles = await cursor.to_list(length=limit)
        return [await self._enrich_article(a, current_user_id) for a in articles]
        
    async def list_all_pending(self):
        cursor = self.collection.find({"status": "pending"}).sort("created_at", 1)
        articles = await cursor.to_list(length=100)
        # Pending view thường cho admin hoặc chính chủ, không cần check like
        return [await self._enrich_article(a) for a in articles]

    async def delete_pending(self, article_id: str, expert_profile_id: str):
        """Chỉ cho phép xóa bài của chính mình và đang ở trạng thái pending"""
        try:
            oid = ObjectId(article_id)
            exp_oid = ObjectId(expert_profile_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid ID format")

        article = await self.collection.find_one({"_id": oid})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        if str(article["expert_id"]) != str(exp_oid):
            raise HTTPException(status_code=403, detail="You can only delete your own articles")
            
        if article["status"] != "pending":
            raise HTTPException(status_code=400, detail="Cannot delete processed articles")

        result = await self.collection.delete_one({"_id": oid})
        return result.deleted_count > 0

    async def update_status(self, article_id: str, status: str, approved_at=None):
        update_data = {"status": status}
        if approved_at:
            update_data["approved_at"] = approved_at
        
        try:
            oid = ObjectId(article_id)
        except:
            oid = article_id

        return await self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": update_data},
            return_document=True
        )
    
    async def list_by_status(self, status: str, limit: int = 100):
        cursor = self.collection.find({"status": status}).sort("created_at", -1)
        articles = await cursor.to_list(length=limit)
        return [await self._enrich_article(a) for a in articles]