from app.models.expert_article_model import ExpertArticle
from bson import ObjectId

class ExpertArticleRepository:
    def __init__(self, db):
        self.collection = db["expert_articles"]

    async def create(self, article_data: dict):
        result = await self.collection.insert_one(article_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def list_by_expert(self, expert_id: str):
        # Try ObjectId first
        results = []
        try:
            results = await self.collection.find({"expert_id": ObjectId(expert_id)}).sort("created_at", -1).to_list(length=100)
        except Exception:
            results = []
        
        # Fallback to string expert_id
        if not results:
            results = await self.collection.find({"expert_id": expert_id}).sort("created_at", -1).to_list(length=100)
        
        return results

    async def list_all_pending(self):
        return await self.collection.find({"status": "pending"}).sort("created_at", 1).to_list(length=100)
    
    async def update_status(self, article_id: str, status: str, approved_at=None):
        update_data = {"status": status}
        if approved_at:
            update_data["approved_at"] = approved_at
        
        # Try ObjectId first
        result = None
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(article_id)},
                {"$set": update_data},
                return_document=True
            )
        except Exception:
            result = None
        
        # Fallback to string _id
        if not result:
            result = await self.collection.find_one_and_update(
                {"_id": article_id},
                {"$set": update_data},
                return_document=True
            )
        
        return result

    async def list_by_status(self, status: str, limit: int = 50):
        """List articles by status"""
        return await self.collection.find({"status": status}).sort("created_at", -1).to_list(length=limit)

    async def list_all(self, limit: int = 50):
        """List all articles"""
        return await self.collection.find().sort("created_at", -1).to_list(length=limit)

