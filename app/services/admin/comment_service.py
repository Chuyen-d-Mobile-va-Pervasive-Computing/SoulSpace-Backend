"""
Service for comment management operations (Admin role only)
"""
from datetime import datetime
from fastapi import HTTPException
from app.repositories.anon_comment_repository import AnonCommentRepository
from app.repositories.moderation_log_repository import ModerationLogRepository
from app.services.common.notification_service import NotificationService
from app.services.common.email_service import EmailService 

class AdminCommentService:
    def __init__(self, db):
        self.db = db
        self.comment_repo = AnonCommentRepository(db)
        self.log_repo = ModerationLogRepository(db)
        self.notification_service = NotificationService(db)
        self.email_service = EmailService()

    async def delete_comment_admin(self, comment_id: str, reason: str, admin_id: str):
        """Admin delete comment (bypass ownership check)"""
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Lấy thông tin user
        user = await self.db["users"].find_one({"_id": comment["user_id"]})
        user_email = user.get("email") if user else None
        username = user.get("username", "User") if user else "User"

        # Xóa comment
        await self.comment_repo.delete(comment_id)

        # Giảm comment_count nếu đã duyệt
        if comment.get("moderation_status") == "Approved":
            await self.db["anon_posts"].update_one(
                {"_id": comment.get("post_id")},
                {"$inc": {"comment_count": -1}}
            )

        # Ghi log
        action_text = f"Deleted by Admin: {reason}" if reason else "Deleted by Admin"
        await self.log_repo.create_log(
            content_id=comment_id,
            content_type="comment",
            user_id=admin_id,
            text=comment.get("content", "")[:200],
            detected_keywords=[],
            action=action_text
        )

        # Gửi thông báo in-app
        await self.notification_service.create_notification(
            user_id=str(comment["user_id"]),
            title="Comment Deleted",
            message=f"Your comment has been deleted by Admin. Reason: {reason}",
            type="alert"
        )

        # Gửi email thông báo xóa bình luận
        if user_email:
            try:
                await self.email_service.send_comment_deleted_email(
                    user_email=user_email,
                    username=username,
                    reason=reason,
                    comment_content=comment.get("content", "")
                )
            except Exception as e:
                print(f"[WARNING] Failed to send comment deletion email to {user_email}: {e}")

        return {
            "message": "Comment deleted and user notified (app + email)",
            "comment_id": comment_id,
            "deleted_by": admin_id,
            "deleted_at": datetime.utcnow().isoformat()
        }