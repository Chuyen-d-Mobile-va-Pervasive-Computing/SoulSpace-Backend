from datetime import datetime
from app.repositories.expert_article_repository import ExpertArticleRepository
from app.models.expert_article_model import ExpertArticle
from bson import ObjectId
from fastapi import HTTPException

class ExpertArticleService:
    def __init__(self, db):
        self.repo = ExpertArticleRepository(db)

    async def create_article(self, expert_id: str, title: str, content: str, image_url: str = None, hashtags: list[str] = []):
        article_data = ExpertArticle(
            expert_id=ObjectId(expert_id),
            title=title,
            content=content,
            image_url=image_url,
            hashtags=hashtags,
            status="pending",
            created_at=datetime.utcnow(),
            like_count=0,
            comment_count=0
        ).dict(by_alias=True)
        
        # Remove generated _id to let Mongo handle it or keep it consistent
        if "_id" in article_data:
            del article_data["_id"]
            
        return await self.repo.create(article_data)

    async def get_expert_articles(self, expert_id: str):
        return await self.repo.list_by_expert(expert_id)

    async def get_feed(self, limit: int = 50):
        return await self.repo.list_approved_feed(limit)

    async def get_article_detail(self, article_id: str):
        article = await self.repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return article

    async def delete_article(self, article_id: str, expert_id: str):
        return await self.repo.delete_pending(article_id, expert_id)
    
    async def update_article_status(self, article_id: str, status: str, approved_at=None):
        return await self.repo.update_status(article_id, status, approved_at)
    
    async def list_articles_by_status(self, status: str, limit: int = 50):
        """List articles filtered by status"""
        return await self.repo.list_by_status(status, limit)

    async def list_all_articles(self, limit: int = 50):
        """List all articles"""
        return await self.repo.list_all(limit)
    
    async def list_pending_articles(self, limit: int = 50):
        """List all pending articles"""
        return await self.repo.list_by_status("pending", limit)