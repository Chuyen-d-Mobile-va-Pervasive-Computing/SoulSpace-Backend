from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.user.user_tree_service import UserTreeService, get_user_tree_service
from app.services.user.anon_post_service import AnonPostService
from app.services.user.journal_service import JournalService
from app.repositories.journal_repository import JournalRepository
from app.services.common.toxic_detection_service import get_toxic_detection_service

router = APIRouter(prefix="/tree", tags=["Mental Tree Share"])

class TreeShareRequest(BaseModel):
    journal_id: Optional[str] = None
    include_journal_excerpt: bool = True
    is_anonymous: bool = True
    custom_message: Optional[str] = None
    hashtags: List[str] = ["mentalTree"]

class TreeShareResponse(BaseModel):
    success: bool = True
    post_id: str
    post_url: str
    message: str
    shared_post: Dict[str, Any]

# Mapping level → URL ảnh cây chính xác (theo yêu cầu mới)
TREE_LEVEL_IMAGES = {
    1: "https://res.cloudinary.com/du0kvnalj/image/upload/v1766410252/level_1_tsepv6.png",
    2: "https://res.cloudinary.com/du0kvnalj/image/upload/v1766410448/level_2_gtuff8.png",
    3: "https://res.cloudinary.com/du0kvnalj/image/upload/v1766410447/level_3_rthww5.png",
    4: "https://res.cloudinary.com/du0kvnalj/image/upload/v1766410445/level_4_ucrxtx.png",
    5: "https://res.cloudinary.com/du0kvnalj/image/upload/v1766410447/level_5_vodjj5.png",
    6: "https://res.cloudinary.com/du0kvnalj/image/upload/v1766410446/level_6_dtxckd.png",
    7: "https://res.cloudinary.com/du0kvnalj/image/upload/v1766410446/level_7_b2remw.png",
    8: "https://res.cloudinary.com/du0kvnalj/image/upload/v1766410446/level_8_ghlaa2.png",
}

@router.post("/share", response_model=TreeShareResponse)
async def share_tree(
    payload: TreeShareRequest,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tree_service: UserTreeService = Depends(get_user_tree_service),
):
    user_oid = ObjectId(current_user["_id"])
    toxic_service = get_toxic_detection_service()

    # 1. Kiểm tra đã tưới cây hôm nay chưa
    tree_status = await tree_service.get_user_tree_status(user_oid)
    if tree_status.get("can_water_today", True):
        raise HTTPException(status_code=400, detail="NO_TREE_ACTION_TODAY")

    # 2. Lấy excerpt từ journal nếu cần
    excerpt = ""
    if payload.journal_id and payload.include_journal_excerpt:
        journal_service = JournalService(JournalRepository(db))
        try:
            journal = await journal_service.get_journal_detail(payload.journal_id, str(current_user["_id"]))
            if journal and journal.text_content:
                excerpt = (journal.text_content[:200] + "...") if len(journal.text_content) > 200 else journal.text_content
        except:
            raise HTTPException(status_code=404, detail="JOURNAL_NOT_FOUND")

    # 3. Generate nội dung post
    level = tree_status["current_level_calculated"]
    xp_current = tree_status["current_xp_in_level"]
    xp_next = tree_status["xp_for_next_level"]
    streak = tree_status["streak_days"]

    content_lines = []
    if payload.custom_message:
        content_lines.append(payload.custom_message.strip())
    content_lines.append("My Mental Tree Progress 🌱")
    content_lines.append(f"• Level: {level}")
    content_lines.append(f"• XP: {xp_current}/{xp_next}")
    content_lines.append(f"• Streak: {streak} days")

    if excerpt:
        content_lines.append("")
        content_lines.append("📖 From my journal:")
        content_lines.append(f'"{excerpt}"')

    content_lines.append("")
    content_lines.append("#mentalTree " + " ".join([f"#{h}" for h in payload.hashtags if h.strip()]))

    full_content = "\n".join(content_lines)

    # 4. Toxic detection
    if await toxic_service.check_health():
        toxic_result = await toxic_service.analyze_text(full_content, threshold=0.5)
        if toxic_result.is_violation:
            raise HTTPException(status_code=400, detail="TOXIC_CONTENT_DETECTED")

    # 5. Ảnh cây theo level – ĐÃ SỬA ĐÚNG URL MỚI
    tree_image_url = TREE_LEVEL_IMAGES.get(level)
    if not tree_image_url:
        # Fallback nếu level > 8 (có thể mở rộng sau)
        tree_image_url = TREE_LEVEL_IMAGES[8]  # Dùng level 8 làm max

    # 6. Tạo bài post trên cộng đồng
    post_service = AnonPostService(db)
    post = await post_service.create_post(
        user_id=str(current_user["_id"]),
        content=full_content,
        is_anonymous=payload.is_anonymous,
        hashtags=["mentalTree"] + [h for h in payload.hashtags if h.strip()],
        image_url=tree_image_url
    )

    # 7. Serialize ObjectId
    def serialize_objectid(obj: Any) -> Any:
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, dict):
            return {k: serialize_objectid(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [serialize_objectid(item) for item in obj]
        return obj

    serialized_post = serialize_objectid(post)

    # 8. Lưu lịch sử share
    post_id_str = str(post["_id"])

    await db.tree_shares.insert_one({
        "user_id": user_oid,
        "journal_id": ObjectId(payload.journal_id) if payload.journal_id else None,
        "post_id": ObjectId(post["_id"]),
        "tree_snapshot": {
            "level": level,
            "xp": xp_current,
            "streak": streak
        },
        "shared_at": datetime.now(timezone.utc),
        "is_anonymous": payload.is_anonymous
    })

    # 9. Trả response
    return TreeShareResponse(
        post_id=post_id_str,
        post_url=f"/anon-posts/{post_id_str}",
        message="Shared successfully!",
        shared_post=serialized_post
    )