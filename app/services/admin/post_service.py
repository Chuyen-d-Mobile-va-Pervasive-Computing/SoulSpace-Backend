# app/services/admin/post_service.py
from datetime import datetime
from fastapi import HTTPException
from app.repositories.anon_post_repository import AnonPostRepository
from app.repositories.moderation_log_repository import ModerationLogRepository
from app.services.common.notification_service import NotificationService
from app.services.common.email_service import EmailService

class AdminPostService:
    def __init__(self, db):
        self.db = db
        self.post_repo = AnonPostRepository(db)
        self.log_repo = ModerationLogRepository(db)
        self.notification_service = NotificationService(db)
        self.email_service = EmailService()

    async def delete_post_admin(self, post_id: str, reason: str, admin_id: str):
        """Admin delete post (bypass ownership check)"""
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Lấy thông tin user để gửi email
        user = await self.db["users"].find_one({"_id": post["user_id"]})
        user_email = user.get("email") if user else None
        username = user.get("username", "User") if user else "User"

        await self.post_repo.delete(post_id)

        # Ghi log
        action_text = f"Deleted by Admin: {reason}" if reason else "Deleted by Admin"
        await self.log_repo.create_log(
            content_id=post_id,
            content_type="post",
            user_id=admin_id,
            text=post.get("content", "")[:200],
            detected_keywords=[],
            action=action_text
        )

        # Gửi thông báo in-app
        await self.notification_service.create_notification(
            user_id=str(post["user_id"]),
            title="Post Deleted",
            message=f"Your post has been deleted by Admin. Reason: {reason}",
            type="alert"
        )

        # Gửi email thông báo xóa bài viết
        if user_email:
            try:
                await self.email_service.send_post_deleted_email(
                    user_email=user_email,
                    username=username,
                    reason=reason
                )
            except Exception as e:
                print(f"[WARNING] Failed to send post deletion email to {user_email}: {e}")

        return {
            "message": "Post deleted and user notified (app + email)",
            "post_id": post_id,
            "deleted_by": admin_id,
            "deleted_at": datetime.utcnow().isoformat()
        }