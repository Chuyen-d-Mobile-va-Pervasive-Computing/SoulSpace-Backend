from datetime import datetime
from app.repositories.notification_repository import NotificationRepository
from app.models.notification_model import Notification
from bson import ObjectId

class NotificationService:
    def __init__(self, db):
        self.repo = NotificationRepository(db)

    async def create_notification(self, user_id: str, title: str, message: str, type: str):
        notification_data = Notification(
            user_id=ObjectId(user_id),
            title=title,
            message=message,
            type=type,
            is_read=False,
            created_at=datetime.utcnow()
        ).dict(by_alias=True)
        
        return await self.repo.create(notification_data)

    async def get_user_notifications(self, user_id: str):
        return await self.repo.list_by_user(user_id)
