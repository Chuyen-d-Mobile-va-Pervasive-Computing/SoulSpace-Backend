import re
from datetime import datetime
from app.repositories.anon_post_repository import AnonPostRepository
from app.models.anon_post_model import AnonPost
from app.repositories.moderation_log_repository import ModerationLogRepository
from app.services.common.notification_service import NotificationService

class AnonPostService:
    def __init__(self, db):
        self.post_repo = AnonPostRepository(db)
        self.log_repo = ModerationLogRepository(db)
        self.keywords_collection = db["sensitive_keywords"]
        self.notification_service = NotificationService(db)

    async def create_post(self, user_id: str, content: str, is_anonymous: bool = True, hashtags: list[str] = []):
        detected = []
        action = "Approved"
        scan_result = "Safe"
        flagged_reason = None

        # --- Load keywords ---
        keywords = await self.keywords_collection.find().to_list(length=1000)

        # --- Kiểm duyệt keyword ---
        for kw in keywords:
            base = kw["keyword"].lower()
            variations = [v.lower() for v in kw.get("variations", [])]
            all_terms = [base] + variations

            for term in all_terms:
                # regex word boundary để tránh match trong từ khác
                if len(term) <= 3:
                    # ví dụ "od", "kms", "die"
                    pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
                else:
                    # cho phép tìm trong chuỗi (slang, cụm dài)
                    pattern = re.compile(re.escape(term), re.IGNORECASE)

                if pattern.search(content):
                    detected.append(term)
                    if kw["severity"] == "hard":
                        action = "Blocked"
                        scan_result = "Unsafe"
                        flagged_reason = f"Hard block keyword detected: {term}"
                    elif kw["severity"] == "soft" and action != "Blocked":
                        action = "Pending"
                        scan_result = "Suspicious"
                        flagged_reason = f"Soft block keyword detected: {term}"

        # --- Kiểm duyệt link ---
        if re.search(r"(https?:\/\/\S+|(?:www\.)?[a-zA-Z0-9-]+\.[a-z]{2,}(\/\S*)?)", content, re.IGNORECASE):
            detected.append("link")
            action = "Blocked"
            scan_result = "Unsafe"
            flagged_reason = "Post contains link"

        # --- Kiểm duyệt số điện thoại ---
        if re.search(r"\b(?:\+?\d[\d\-\s]{8,14}\d)\b", content):
            detected.append("phone_number")
            action = "Blocked"
            scan_result = "Unsafe"
            flagged_reason = "Post contains phone number"

        # --- Tạo post ---
        post_data = AnonPost(
            user_id=user_id,
            content=content,
            is_anonymous=is_anonymous,
            hashtags=hashtags,
            created_at=datetime.utcnow(),
            moderation_status=action,
            ai_scan_result=scan_result,
            flagged_reason=flagged_reason,
            like_count=0,
            comment_count=0,
        ).dict(by_alias=True)

        new_post = await self.post_repo.create(post_data)

        # --- Log moderation ---
        await self.log_repo.create_log(
            content_id=new_post["_id"],
            content_type="post",
            user_id=user_id,
            text=content,
            detected_keywords=detected,
            action=action
        )
        new_post["detected_keywords"] = detected

        # --- Notification Logic ---
        if action == "Blocked":
            await self.notification_service.create_notification(
                user_id=user_id,
                title="Bài viết bị chặn",
                message=f"Bài viết của bạn đã bị chặn vì lý do: {flagged_reason}. Nếu bạn cần giúp đỡ, hãy liên hệ với chuyên gia.",
                type="alert"
            )
        elif action == "Pending":
             await self.notification_service.create_notification(
                user_id=user_id,
                title="Bài viết đang chờ duyệt",
                message=f"Bài viết của bạn có nội dung cần xem xét: {flagged_reason}. Chúng tôi sẽ thông báo khi có kết quả.",
                type="system"
            )
        
        return new_post
    
    async def delete_post(self, user_id: str, post_id: str):
        # Lấy và xóa bài viết
        post = await self.post_repo.delete(post_id)

        # Ghi log moderation
        await self.log_repo.create_log(
            content_id=post_id,
            content_type="post",
            user_id=user_id,
            text=post["content"],
            detected_keywords=[],
            action="Deleted"
        )
        return {"deleted": True, "post_id": post_id}