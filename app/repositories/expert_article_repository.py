from app.models.expert_article_model import ExpertArticle
from bson import ObjectId

class ExpertArticleRepository:
    def __init__(self, db):
        self.collection = db["expert_articles"]

    async def create(self, article_data: dict):
        result = await self.collection.insert_one(article_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def list_by_expert(self, expert_id: str):
        return await self.collection.find({"expert_id": ObjectId(expert_id)}).sort("created_at", -1).to_list(length=100)

    async def list_all_pending(self):
        return await self.collection.find({"status": "pending"}).sort("created_at", 1).to_list(length=100)
    
    async def update_status(self, article_id: str, status: str, approved_at=None):
        update_data = {"status": status}
        if approved_at:
            update_data["approved_at"] = approved_at
            
        await self.collection.update_one(
            {"_id": ObjectId(article_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(article_id)})
