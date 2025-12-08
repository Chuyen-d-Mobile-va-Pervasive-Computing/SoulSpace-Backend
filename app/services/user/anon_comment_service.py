from datetime import datetime
from app.repositories.anon_comment_repository import AnonCommentRepository
from app.repositories.anon_post_repository import AnonPostRepository
from app.models.anon_comment_model import AnonComment
from app.repositories.moderation_log_repository import ModerationLogRepository
from bson import ObjectId
import re

class AnonCommentService:
    def __init__(self, db):
        self.comment_repo = AnonCommentRepository(db)
        self.post_repo = AnonPostRepository(db)
        self.log_repo = ModerationLogRepository(db)
        self.keywords_collection = db["sensitive_keywords"]

    async def create_comment(self, user_id: str, post_id: str, content: str, is_preset: bool):
        detected = []
        action = "Approved"
        scan_result = "Safe"
        flagged_reason = None

        # --- load sensitive keywords ---
        keywords = await self.keywords_collection.find().to_list(length=1000)

        for kw in keywords:
            base = kw["keyword"].lower()
            variations = [v.lower() for v in kw.get("variations", [])]
            all_terms = [base] + variations
            for term in all_terms:
                if re.search(rf"\b{re.escape(term)}\b", content, re.IGNORECASE):
                    detected.append(term)
                    if kw["severity"] == "hard":
                        action = "Blocked"
                        scan_result = "Unsafe"
                        flagged_reason = f"Hard block keyword detected: {term}"
                    elif kw["severity"] == "soft" and action != "Blocked":
                        action = "Pending"
                        scan_result = "Suspicious"
                        flagged_reason = f"Soft block keyword detected: {term}"


        # --- build comment object ---
        # Ensure user_id is ObjectId for consistency
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        comment_data = AnonComment(
            post_id=ObjectId(post_id),
            user_id=user_oid,
            content=content,
            created_at=datetime.utcnow(),
            moderation_status=action,
            is_preset=is_preset
        ).dict(by_alias=True)
        
        # Remove _id to let MongoDB generate proper ObjectId
        if "_id" in comment_data:
            del comment_data["_id"]
        
        # Ensure ObjectId types for database
        comment_data["user_id"] = user_oid
        comment_data["post_id"] = ObjectId(post_id)

        new_comment = await self.comment_repo.create(comment_data)

        # --- update comment_count của post ---
        if action == "Approved":
            await self.post_repo.increment_comment_count(post_id)

        # --- log moderation ---
        await self.log_repo.create_log(
            content_id=new_comment["_id"],
            content_type="comment",
            user_id=user_id,
            text=content,
            detected_keywords=detected,
            action=action
        )

        return new_comment
    
    async def increment_comment_count(self, post_id: str):
        await self.collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"comment_count": 1}}
        )

    async def delete_comment(self, comment_id: str, user_id):
        """Xóa comment - chỉ owner mới được xóa."""
        from fastapi import HTTPException
        
        # Convert user_id to string
        user_id_str = str(user_id)
        
        # Get comment first to check ownership
        comment = await self.comment_repo.get_by_id(comment_id)
        
        # Check ownership
        comment_user_id = str(comment.get("user_id", ""))
        if comment_user_id != user_id_str:
            raise HTTPException(status_code=403, detail="You can only delete your own comments")
        
        # Delete comment
        deleted_comment = await self.comment_repo.delete(comment_id)

        # Giảm comment_count nếu comment trước đó đã Approved
        if deleted_comment.get("moderation_status") == "Approved":
            await self.post_repo.decrement_comment_count(str(deleted_comment.get("post_id")))

        # Log moderation
        await self.log_repo.create_log(
            content_id=comment_id,
            content_type="comment",
            user_id=user_id_str,
            text=deleted_comment.get("content", ""),
            detected_keywords=[],
            action="Deleted"
        )
        return {"deleted": True, "comment_id": comment_id}