"""
Admin role API endpoints.
These endpoints are for admin-only operations.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.core.permissions import Role, require_role
from app.core.database import get_db
from app.services.user.anon_post_service import AnonPostService
from app.services.user.report_service import ReportService
from app.services.expert.expert_article_service import ExpertArticleService
from app.services.common.notification_service import NotificationService
from app.schemas.user.anon_post_schema import AnonPostResponse
from app.schemas.user.report_schema import ReportResponse
from app.schemas.expert.expert_article_schema import ExpertArticleResponse

router = APIRouter(prefix="/admin", tags=["🔧 Admin - Management (Quản trị)"])

@router.get("/health")
async def admin_health_check():
    return {"status": "healthy", "role": "admin"}

# --- Post Management ---
@router.get("/posts", response_model=list[AnonPostResponse])
@require_role(Role.ADMIN)
async def list_all_posts(db=Depends(get_db)):
    service = AnonPostService(db)
    return await service.post_repo.list()

@router.delete("/posts/{post_id}")
@require_role(Role.ADMIN)
async def delete_post(post_id: str, reason: str, db=Depends(get_db), user=Depends(get_current_user)):
    service = AnonPostService(db)
    notif_service = NotificationService(db)
    
    # Get post to find owner
    post = await service.post_repo.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    await service.delete_post(user["_id"], post_id)
    
    # Notify user
    await notif_service.create_notification(
        user_id=str(post["user_id"]),
        title="Bài viết bị xóa",
        message=f"Bài viết của bạn đã bị xóa bởi Admin. Lý do: {reason}",
        type="alert"
    )
    return {"message": "Post deleted and user notified"}

# --- Report Management ---
@router.get("/reports", response_model=list[ReportResponse])
@require_role(Role.ADMIN)
async def list_reports(db=Depends(get_db)):
    service = ReportService(db)
    return await service.list_reports()

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
    # Simple stats for now
    users_count = await db["users"].count_documents({})
    posts_count = await db["anon_posts"].count_documents({})
    reports_count = await db["reports"].count_documents({"status": "pending"})
    
    return {
        "total_users": users_count,
        "total_posts": posts_count,
        "pending_reports": reports_count
    }
