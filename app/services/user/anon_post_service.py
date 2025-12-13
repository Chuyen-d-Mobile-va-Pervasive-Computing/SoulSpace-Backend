import re
from datetime import datetime
from typing import Optional
from app.repositories.anon_post_repository import AnonPostRepository
from app.models.anon_post_model import AnonPost
from app.repositories.moderation_log_repository import ModerationLogRepository
from app.services.common.notification_service import NotificationService
from app.services.common.toxic_detection_service import get_toxic_detection_service

class AnonPostService:
    def __init__(self, db):
        self.db = db
        self.post_repo = AnonPostRepository(db)
        self.log_repo = ModerationLogRepository(db)
        self.notification_service = NotificationService(db)
        self.toxic_service = get_toxic_detection_service()

    async def create_post(self, user_id: str, content: str, is_anonymous: bool = True, hashtags: list[str] = [], image_url: str = None):
        """
        Tạo bài viết mới với AI toxic detection.
        - is_anonymous=True: Đăng ẩn danh
        - is_anonymous=False: Đăng bằng tên tài khoản
        - image_url: URL ảnh đính kèm (optional)
        """
        from bson import ObjectId
        
        # Default values
        action = "Approved"
        scan_result = "Safe"
        flagged_reason = None
        toxic_labels = []
        toxic_confidence = 0.0
        toxic_predictions = {}
        
        # --- AI Toxic Detection ---
        try:
            # Check if toxic API is available
            is_api_healthy = await self.toxic_service.check_health()
            
            if is_api_healthy:
                # Use AI model for toxic detection
                toxic_result = await self.toxic_service.analyze_text(content, threshold=0.5)
                
                toxic_labels = toxic_result.toxic_labels
                toxic_confidence = toxic_result.confidence
                toxic_predictions = toxic_result.predictions
                
                if toxic_result.is_violation:
                    # Check severity based on toxic types
                    severe_types = ["severe_toxic", "threat", "identity_hate"]
                    has_severe = any(label in toxic_labels for label in severe_types)
                    
                    if has_severe or toxic_confidence >= 0.8:
                        action = "Blocked"
                        scan_result = "Unsafe"
                        flagged_reason = f"AI detected toxic content: {', '.join(toxic_labels)} (confidence: {toxic_confidence:.2%})"
                    else:
                        action = "Pending"
                        scan_result = "Suspicious"
                        flagged_reason = f"AI flagged for review: {', '.join(toxic_labels)} (confidence: {toxic_confidence:.2%})"
            else:
                # Fallback: API not available, approve but flag for manual review
                scan_result = "Not Scanned"
                flagged_reason = "AI service unavailable - manual review required"
                
        except Exception as e:
            # Error in AI detection - approve but log error
            scan_result = "Error"
            flagged_reason = f"AI scan error: {str(e)}"
        
        # --- Basic content validation (keep these checks) ---
        # Check for links
        if re.search(r"(https?:\/\/\S+|(?:www\.)?[a-zA-Z0-9-]+\.[a-z]{2,}(\/\S*)?)", content, re.IGNORECASE):
            if action == "Approved":
                action = "Pending"
                scan_result = "Suspicious"
            flagged_reason = (flagged_reason or "") + " | Contains link"
        
        # Check for phone numbers
        if re.search(r"\b(?:\+?\d[\d\-\s]{8,14}\d)\b", content):
            if action == "Approved":
                action = "Pending"
                scan_result = "Suspicious"
            flagged_reason = (flagged_reason or "") + " | Contains phone number"
        
        # --- Create post ---
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        post_data = AnonPost(
            user_id=user_oid,
            content=content,
            is_anonymous=is_anonymous,
            hashtags=hashtags,
            image_url=image_url,
            created_at=datetime.utcnow(),
            moderation_status=action,
            ai_scan_result=scan_result,
            flagged_reason=flagged_reason,
            like_count=0,
            comment_count=0,
        ).dict(by_alias=True)
        
        # Add AI analysis fields
        post_data["toxic_labels"] = toxic_labels
        post_data["toxic_confidence"] = toxic_confidence
        post_data["toxic_predictions"] = toxic_predictions
        
        # Remove the auto-generated _id and let MongoDB generate a proper ObjectId
        if "_id" in post_data:
            del post_data["_id"]
        
        # Restore user_id as ObjectId (dict() serializes it to string)
        post_data["user_id"] = user_oid

        new_post = await self.post_repo.create(post_data)

        # --- Log moderation ---
        await self.log_repo.create_log(
            content_id=new_post["_id"],
            content_type="post",
            user_id=user_id,
            text=content,
            detected_keywords=toxic_labels,
            action=action
        )
        
        # Enrich post với author info
        enriched_post = await self.post_repo._enrich_post(new_post, str(user_id))
        enriched_post["detected_keywords"] = toxic_labels
        enriched_post["toxic_confidence"] = toxic_confidence
        enriched_post["toxic_predictions"] = toxic_predictions

        # --- Notification Logic ---
        if action == "Blocked":
            await self.notification_service.create_notification(
                user_id=user_id,
                title="Bài viết bị chặn",
                message=f"Bài viết của bạn đã bị chặn vì phát hiện nội dung không phù hợp. Nếu bạn cần hỗ trợ, hãy liên hệ với chuyên gia tâm lý.",
                type="alert"
            )
        elif action == "Pending":
             await self.notification_service.create_notification(
                user_id=user_id,
                title="Bài viết đang chờ duyệt",
                message="Bài viết của bạn đang được xem xét. Chúng tôi sẽ thông báo khi có kết quả.",
                type="system"
            )
        
        return enriched_post

    async def list_posts(self, limit: int = 20, current_user_id: Optional[str] = None) -> list:
        """
        Lấy danh sách bài viết đã được duyệt.
        Nếu có current_user_id, sẽ check is_liked và is_owner.
        """
        return await self.post_repo.list(limit=limit, current_user_id=current_user_id)

    async def get_my_posts(self, user_id: str, limit: int = 50) -> list:
        """
        Lấy tất cả bài viết của user (bao gồm Pending, Blocked).
        """
        return await self.post_repo.list_by_user(user_id=user_id, limit=limit)

    async def get_post_detail(self, post_id: str, current_user_id: Optional[str] = None) -> dict:
        """
        Lấy chi tiết một bài viết với author info.
        """
        return await self.post_repo.get_by_id_with_author(post_id=post_id, current_user_id=current_user_id)
    
    async def delete_post(self, user_id, post_id: str):
        """Xóa bài viết (chỉ owner mới được xóa)."""
        from bson import ObjectId
        from fastapi import HTTPException
        
        # Convert user_id to string for comparison
        user_id_str = str(user_id)
        
        # Kiểm tra quyền sở hữu
        post = await self.post_repo.get_by_id(post_id)
        post_user_id = str(post.get("user_id", ""))
        
        if post_user_id != user_id_str:
            raise HTTPException(status_code=403, detail="You can only delete your own posts")
        
        # Xóa bài viết
        deleted_post = await self.post_repo.delete(post_id)

        # Ghi log moderation
        await self.log_repo.create_log(
            content_id=post_id,
            content_type="post",
            user_id=user_id_str,
            text=deleted_post["content"],
            detected_keywords=[],
            action="Deleted"
        )
        return {"deleted": True, "post_id": post_id}