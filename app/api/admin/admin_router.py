"""
Admin role API endpoints.
These endpoints are for admin-only operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.dependencies import get_current_user
from app.core.permissions import Role, require_role
from app.core.database import get_db
from app.services.user.anon_post_service import AnonPostService
from app.services.user.anon_comment_service import AnonCommentService
from app.services.user.report_service import ReportService
from app.services.expert.expert_article_service import ExpertArticleService
from app.services.common.notification_service import NotificationService
from app.schemas.user.anon_post_schema import AnonPostResponse
from app.schemas.user.report_schema import ReportResponse
from app.schemas.expert.expert_article_schema import ExpertArticleResponse
from bson import ObjectId

router = APIRouter(prefix="/admin", tags=["🔧 Admin - Management (Quản trị)"])

@router.get("/health")
async def admin_health_check():
    return {"status": "healthy", "role": "admin"}

# --- Post Management ---
@router.get("/posts")
@require_role(Role.ADMIN)
async def list_all_posts(
    status: str = Query(None, description="Filter: Approved, Pending, Blocked"),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db)
):
    """
    Lấy danh sách bài viết (Admin xem được tất cả, bao gồm username của bài ẩn danh).
    """
    collection = db["anon_posts"]
    users_collection = db["users"]
    
    query = {}
    if status:
        query["moderation_status"] = status
    
    cursor = collection.find(query).sort("created_at", -1).limit(limit)
    posts = await cursor.to_list(length=limit)
    
    # Enrich với username cho admin (luôn hiển thị, kể cả ẩn danh)
    enriched_posts = []
    for post in posts:
        user = await users_collection.find_one(
            {"_id": post.get("user_id")},
            {"username": 1, "email": 1}
        )
        post["_id"] = str(post["_id"])
        post["user_id"] = str(post.get("user_id", ""))
        post["username"] = user.get("username", "Unknown") if user else "Unknown"
        post["user_email"] = user.get("email", "") if user else ""
        post["author_display"] = "Ẩn danh" if post.get("is_anonymous") else post["username"]
        enriched_posts.append(post)
    
    return enriched_posts

@router.delete("/posts/{post_id}")
@require_role(Role.ADMIN)
async def delete_post(post_id: str, reason: str, db=Depends(get_db), user=Depends(get_current_user)):
    """Xóa bài viết và gửi thông báo đến user."""
    service = AnonPostService(db)
    notif_service = NotificationService(db)
    
    # Get post to find owner
    post = await service.post_repo.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Delete post (bypass owner check for admin)
    await service.post_repo.delete(post_id)
    
    # Notify user
    await notif_service.create_notification(
        user_id=str(post["user_id"]),
        title="Bài viết bị xóa",
        message=f"Bài viết của bạn đã bị xóa bởi Admin. Lý do: {reason}",
        type="alert"
    )
    return {"message": "Post deleted and user notified"}

# --- Comment Management ---
@router.get("/comments")
@require_role(Role.ADMIN)
async def list_all_comments(
    post_id: str = Query(None, description="Filter by post_id"),
    status: str = Query(None, description="Filter: Approved, Pending, Blocked"),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db)
):
    """Lấy danh sách comments (Admin)."""
    collection = db["anon_comments"]
    users_collection = db["users"]
    
    query = {}
    if post_id:
        query["post_id"] = ObjectId(post_id)
    if status:
        query["moderation_status"] = status
    
    cursor = collection.find(query).sort("created_at", -1).limit(limit)
    comments = await cursor.to_list(length=limit)
    
    enriched_comments = []
    for comment in comments:
        user = await users_collection.find_one(
            {"_id": comment.get("user_id")},
            {"username": 1}
        )
        comment["_id"] = str(comment["_id"])
        comment["post_id"] = str(comment.get("post_id", ""))
        comment["user_id"] = str(comment.get("user_id", ""))
        comment["username"] = user.get("username", "Unknown") if user else "Unknown"
        enriched_comments.append(comment)
    
    return enriched_comments

@router.delete("/comments/{comment_id}")
@require_role(Role.ADMIN)
async def delete_comment(comment_id: str, reason: str, db=Depends(get_db), user=Depends(get_current_user)):
    """Xóa comment và gửi thông báo đến user."""
    service = AnonCommentService(db)
    notif_service = NotificationService(db)
    
    # Get comment
    comment = await service.comment_repo.get_by_id(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Delete comment (bypass owner check for admin)
    await service.comment_repo.delete(comment_id)
    
    # Decrement comment count on post
    await db["anon_posts"].update_one(
        {"_id": comment.get("post_id")},
        {"$inc": {"comment_count": -1}}
    )
    
    # Notify user
    await notif_service.create_notification(
        user_id=str(comment["user_id"]),
        title="Bình luận bị xóa",
        message=f"Bình luận của bạn đã bị xóa bởi Admin. Lý do: {reason}",
        type="alert"
    )
    return {"message": "Comment deleted and user notified"}

# --- Report Management ---
@router.get("/reports", response_model=list[ReportResponse])
@require_role(Role.ADMIN)
async def list_reports(
    status: str = Query(None, description="Filter: pending, resolved, dismissed"),
    db=Depends(get_db)
):
    """Lấy danh sách reports."""
    service = ReportService(db)
    return await service.list_reports(status=status)

@router.put("/reports/{report_id}/resolve")
@require_role(Role.ADMIN)
async def resolve_report(
    report_id: str,
    action: str = Query(..., description="Action: delete_content, warn_user, dismiss"),
    db=Depends(get_db)
):
    """Xử lý report."""
    service = ReportService(db)
    return await service.resolve_report(report_id, action)

# --- Expert Article Management ---
@router.get("/expert-articles/pending", response_model=list[ExpertArticleResponse])
@require_role(Role.ADMIN)
async def list_pending_articles(db=Depends(get_db)):
    service = ExpertArticleService(db)
    return await service.list_pending_articles()

@router.put("/expert-articles/{article_id}/status")
@require_role(Role.ADMIN)
async def update_article_status(article_id: str, status: str, db=Depends(get_db)):
    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    service = ExpertArticleService(db)
    article = await service.update_article_status(article_id, status)
    
    # Notify expert
    notif_service = NotificationService(db)
    await notif_service.create_notification(
        user_id=str(article["expert_id"]),
        title=f"Bài viết đã được {status}",
        message=f"Bài viết '{article['title']}' của bạn đã được {status}.",
        type="system"
    )
    
    return article

# --- Statistics ---
@router.get("/stats")
@require_role(Role.ADMIN)
async def get_stats(db=Depends(get_db)):
    """Thống kê tổng quan hệ thống."""
    users_count = await db["users"].count_documents({})
    experts_count = await db["users"].count_documents({"role": "expert"})
    posts_count = await db["anon_posts"].count_documents({})
    posts_pending = await db["anon_posts"].count_documents({"moderation_status": "Pending"})
    posts_blocked = await db["anon_posts"].count_documents({"moderation_status": "Blocked"})
    comments_count = await db["anon_comments"].count_documents({})
    reports_pending = await db["reports"].count_documents({"status": "pending"})
    articles_pending = await db["expert_articles"].count_documents({"status": "pending"})
    
    return {
        "users": {
            "total": users_count,
            "experts": experts_count
        },
        "posts": {
            "total": posts_count,
            "pending": posts_pending,
            "blocked": posts_blocked
        },
        "comments": {
            "total": comments_count
        },
        "reports": {
            "pending": reports_pending
        },
        "expert_articles": {
            "pending": articles_pending
        }
    }

