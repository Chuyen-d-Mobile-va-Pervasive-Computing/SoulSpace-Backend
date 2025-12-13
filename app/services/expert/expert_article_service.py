from datetime import datetime
from app.repositories.expert_article_repository import ExpertArticleRepository
from app.models.expert_article_model import ExpertArticle
from bson import ObjectId

class ExpertArticleService:
    def __init__(self, db):
        self.repo = ExpertArticleRepository(db)

    async def create_article(self, expert_id: str, title: str, content: str, image_url: str = None):
        article_data = ExpertArticle(
            expert_id=ObjectId(expert_id),
            title=title,
            content=content,
            image_url=image_url,
            status="pending",
            created_at=datetime.utcnow()
        ).dict(by_alias=True)
        
        return await self.repo.create(article_data)

    async def get_expert_articles(self, expert_id: str):
        return await self.repo.list_by_expert(expert_id)

    async def list_pending_articles(self):
        return await self.repo.list_all_pending()

    async def update_article_status(self, article_id: str, status: str):
        approved_at = datetime.utcnow() if status == "approved" else None
        return await self.repo.update_status(article_id, status, approved_at)

    async def list_articles_by_status(self, status: str, limit: int = 50):
        """List articles filtered by status (pending, approved, rejected)"""
        return await self.repo.list_by_status(status, limit)

    async def list_all_articles(self, limit: int = 50):
        """List all articles"""
        return await self.repo.list_all(limit)

