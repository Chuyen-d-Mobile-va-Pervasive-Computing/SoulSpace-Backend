"""
Admin role API endpoints.
These endpoints are for admin-only operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from app.core.dependencies import get_current_user
from app.core.permissions import Role, require_role
from app.core.database import get_db
from app.core.security import hash_password
from app.services.user.anon_post_service import AnonPostService
from app.services.user.anon_comment_service import AnonCommentService
from app.services.user.report_service import ReportService
from app.services.expert.expert_article_service import ExpertArticleService
from app.services.common.notification_service import NotificationService
from app.schemas.user.anon_post_schema import AnonPostResponse
from app.schemas.user.report_schema import ReportResponse
from app.schemas.expert.expert_article_schema import ExpertArticleResponse
from bson import ObjectId
from datetime import datetime, timedelta, date
from typing import Optional, Literal
import re


# Security scheme for Swagger UI lock icon
security = HTTPBearer()


# Schema for creating admin/expert by admin
class CreateUserByAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: str = Field(default="NewUser", max_length=30)
    role: str = Field(default="admin", description="Role: admin or expert")
    
    @validator("password")
    def validate_password(cls, v):
        if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", v):
            raise ValueError("Password must be at least 8 characters with 1 uppercase and 1 number")
        return v
    
    @validator("role")
    def validate_role(cls, v):
        if v not in ["admin", "expert"]:
            raise ValueError("Role must be 'admin' or 'expert'")
        return v


# Keep old schema for backward compatibility
CreateAdminRequest = CreateUserByAdminRequest


# Router với Security dependency - Swagger sẽ hiển thị 🔒
router = APIRouter(
    prefix="/admin", 
    tags=["🔧 Admin - Management (Quản trị)"],
    dependencies=[Security(security)]  # Thêm lock icon cho tất cả endpoints
)

@router.get("/health")
async def admin_health_check():
    return {"status": "healthy", "role": "admin"}


# --- Admin User Management ---
@router.post("/users/create")
@require_role(Role.ADMIN)
async def create_user_by_admin(
    data: CreateUserByAdminRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Tạo tài khoản Admin hoặc Expert mới.
    Chỉ Admin hiện tại mới có quyền tạo.
    
    - role: "admin" hoặc "expert"
    """
    users_collection = db["users"]
    
    # Check email exists
    existing = await users_collection.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Check username exists
    existing_username = await users_collection.find_one({"username": data.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user with specified role
    user_data = {
        "username": data.username,
        "email": data.email,
        "password": hash_password(data.password),
        "role": data.role,  # Use role from request
        "total_points": 0,
        "created_at": datetime.utcnow(),
        "created_by": str(current_user["_id"]),
        "last_login_at": None
    }
    
    # Additional fields for expert
    if data.role == "expert":
        user_data["expert_status"] = "approved"  # Auto-approve when created by admin
    
    result = await users_collection.insert_one(user_data)
    
    return {
        "message": f"{data.role.capitalize()} created successfully",
        "user_id": str(result.inserted_id),
        "email": data.email,
        "username": data.username,
        "role": data.role,
        "created_by": str(current_user["_id"])
    }


# Backward compatibility - keep old endpoint name
@router.post("/users/create-admin")
@require_role(Role.ADMIN)
async def create_admin_user(
    data: CreateAdminRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Alias for /users/create - backward compatibility."""
    # Force role to admin for this endpoint
    data.role = "admin"
    return await create_user_by_admin(data, db, current_user)


@router.get("/users")
@require_role(Role.ADMIN)
async def list_all_users(
    role: str = Query(None, description="Filter by role: user, admin, expert"),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lấy danh sách tất cả users."""
    users_collection = db["users"]
    
    query = {}
    if role:
        query["role"] = role
    
    cursor = users_collection.find(query, {"password": 0}).sort("created_at", -1).limit(limit)
    users = await cursor.to_list(length=limit)
    
    for user in users:
        user["_id"] = str(user["_id"])
    
    return users



# --- Post Management ---
@router.get("/posts")
@require_role(Role.ADMIN)
async def list_all_posts(
    status: str = Query(None, description="Filter: Approved, Pending, Blocked"),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
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
    db=Depends(get_db),
    current_user=Depends(get_current_user)
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
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lấy danh sách reports."""
    service = ReportService(db)
    return await service.list_reports(status=status)

@router.put("/reports/{report_id}/resolve")
@require_role(Role.ADMIN)
async def resolve_report(
    report_id: str,
    action: str = Query(..., description="Action: delete_content, warn_user, dismiss"),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Xử lý report.
    
    Actions:
    - delete_content: Xóa nội dung bị báo cáo
    - warn_user: Cảnh báo người dùng
    - dismiss: Bỏ qua báo cáo
    """
    service = ReportService(db)
    try:
        return await service.resolve_report(report_id, action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# --- Expert Article Management ---
@router.get("/expert-articles/pending", response_model=list[ExpertArticleResponse])
@require_role(Role.ADMIN)
async def list_pending_articles(db=Depends(get_db), current_user=Depends(get_current_user)):
    service = ExpertArticleService(db)
    return await service.list_pending_articles()

@router.put("/expert-articles/{article_id}/status")
@require_role(Role.ADMIN)
async def update_article_status(article_id: str, status: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'approved' or 'rejected'")
        
    service = ExpertArticleService(db)
    article = await service.update_article_status(article_id, status)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Notify expert (with error handling)
    try:
        notif_service = NotificationService(db)
        await notif_service.create_notification(
            user_id=str(article["expert_id"]),
            title=f"Bài viết đã được {status}",
            message=f"Bài viết '{article['title']}' của bạn đã được {status}.",
            type="system"
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Warning: Failed to send notification: {e}")
    
    # Convert ObjectIds to strings for JSON response
    article["_id"] = str(article["_id"])
    article["expert_id"] = str(article["expert_id"])
    
    return article

# --- Statistics ---
@router.get("/stats")
@require_role(Role.ADMIN)
async def get_stats(
    period: Optional[Literal["today", "week", "month", "all"]] = Query(None, description="Khoảng thời gian: today (hôm nay), week (7 ngày), month (30 ngày), all (tất cả)"),
    date: Optional[str] = Query(None, description="Chọn ngày cụ thể (format: YYYY-MM-DD), ví dụ: 2025-12-01"),
    db=Depends(get_db), 
    current_user=Depends(get_current_user)
):
    """
    Thống kê tổng quan hệ thống.
    
    **Cách 1 - Dùng period:**
    - period=today: Thống kê hôm nay
    - period=week: Thống kê 7 ngày qua
    - period=month: Thống kê 30 ngày qua
    - period=all hoặc không truyền: Thống kê tất cả
    
    **Cách 2 - Chọn ngày cụ thể:**
    - date=2025-12-01: Thống kê của ngày 01/12/2025
    
    Lưu ý: Nếu truyền cả period và date, date sẽ được ưu tiên.
    """
    
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    filter_start = None
    filter_end = None
    
    # Priority: date > period
    if date:
        try:
            selected_date = datetime.strptime(date, "%Y-%m-%d")
            filter_start = selected_date
            filter_end = selected_date + timedelta(days=1) - timedelta(seconds=1)
            period_label = f"Ngày {date}"
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD (ví dụ: 2025-12-01)")
    elif period == "today":
        filter_start = today_start
        filter_end = now
        period_label = "Hôm nay"
    elif period == "week":
        filter_start = now - timedelta(days=7)
        filter_end = now
        period_label = "7 ngày qua"
    elif period == "month":
        filter_start = now - timedelta(days=30)
        filter_end = now
        period_label = "30 ngày qua"
    else:
        period_label = "Tất cả"
    
    has_filter = filter_start is not None
    
    async def count_docs(collection: str, extra_query: dict = None, date_field: str = "created_at"):
        """Count documents with optional date filter"""
        query = extra_query.copy() if extra_query else {}
        
        if filter_start and filter_end:
            query[date_field] = {"$gte": filter_start, "$lte": filter_end}
        
        return await db[collection].count_documents(query)
    
    # Users statistics
    users_total = await db["users"].count_documents({})
    users_in_period = await count_docs("users") if has_filter else users_total
    experts_total = await db["users"].count_documents({"role": "expert"})
    experts_in_period = await count_docs("users", {"role": "expert"}) if has_filter else experts_total
    
    # Posts statistics  
    posts_total = await db["anon_posts"].count_documents({})
    posts_in_period = await count_docs("anon_posts") if has_filter else posts_total
    posts_pending = await db["anon_posts"].count_documents({"moderation_status": "Pending"})
    posts_blocked = await db["anon_posts"].count_documents({"moderation_status": "Blocked"})
    
    # Comments statistics
    comments_total = await db["anon_comments"].count_documents({})
    comments_in_period = await count_docs("anon_comments") if has_filter else comments_total
    
    # Reports statistics
    reports_total = await db["reports"].count_documents({})
    reports_in_period = await count_docs("reports") if has_filter else reports_total
    reports_pending = await db["reports"].count_documents({"status": "pending"})
    reports_resolved = await db["reports"].count_documents({"status": "resolved"})
    reports_rejected = await db["reports"].count_documents({"status": "rejected"})
    
    # Expert articles statistics
    articles_total = await db["expert_articles"].count_documents({})
    articles_in_period = await count_docs("expert_articles") if has_filter else articles_total
    articles_pending = await db["expert_articles"].count_documents({"status": "pending"})
    articles_approved = await db["expert_articles"].count_documents({"status": "approved"})
    articles_rejected = await db["expert_articles"].count_documents({"status": "rejected"})
    
    result = {
        "period": period_label,
        "generated_at": now.isoformat(),
        "users": {
            "total": users_total,
            "in_period": users_in_period if has_filter else None,
            "experts": experts_total,
            "experts_in_period": experts_in_period if has_filter else None
        },
        "posts": {
            "total": posts_total,
            "in_period": posts_in_period if has_filter else None,
            "pending": posts_pending,
            "blocked": posts_blocked
        },
        "comments": {
            "total": comments_total,
            "in_period": comments_in_period if has_filter else None
        },
        "reports": {
            "total": reports_total,
            "in_period": reports_in_period if has_filter else None,
            "pending": reports_pending,
            "resolved": reports_resolved,
            "rejected": reports_rejected
        },
        "expert_articles": {
            "total": articles_total,
            "in_period": articles_in_period if has_filter else None,
            "pending": articles_pending,
            "approved": articles_approved,
            "rejected": articles_rejected
        }
    }
    
    return result



