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


@router.get("/posts/pending")
@require_role(Role.ADMIN)
async def list_pending_posts(
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lấy danh sách bài viết đang chờ duyệt (Pending)."""
    collection = db["anon_posts"]
    users_collection = db["users"]
    
    cursor = collection.find({"moderation_status": "Pending"}).sort("created_at", -1).limit(limit)
    posts = await cursor.to_list(length=limit)
    
    enriched_posts = []
    for post in posts:
        user = await users_collection.find_one({"_id": post.get("user_id")}, {"username": 1, "email": 1})
        post["_id"] = str(post["_id"])
        post["user_id"] = str(post.get("user_id", ""))
        post["username"] = user.get("username", "Unknown") if user else "Unknown"
        enriched_posts.append(post)
    
    return enriched_posts


@router.get("/posts/approved")
@require_role(Role.ADMIN)
async def list_approved_posts(
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lấy danh sách bài viết đã duyệt (Approved)."""
    collection = db["anon_posts"]
    
    cursor = collection.find({"moderation_status": "Approved"}).sort("created_at", -1).limit(limit)
    posts = await cursor.to_list(length=limit)
    
    for post in posts:
        post["_id"] = str(post["_id"])
        post["user_id"] = str(post.get("user_id", ""))
    
    return posts


@router.get("/posts/moderation")
@require_role(Role.ADMIN)
async def list_posts_for_moderation(
    status: str = Query(None, description="Filter: Approved, Pending, Blocked"),
    risk_level: str = Query(None, description="Filter by AI risk level"),
    sentiment: str = Query(None, description="Filter by sentiment"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lấy danh sách bài viết cho moderation với các bộ lọc nâng cao."""
    collection = db["anon_posts"]
    users_collection = db["users"]
    
    query = {}
    if status:
        query["moderation_status"] = status
    if risk_level:
        query["ai_risk_level"] = risk_level
    if sentiment:
        query["ai_sentiment"] = sentiment
    
    total = await collection.count_documents(query)
    cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    posts = await cursor.to_list(length=limit)
    
    enriched_posts = []
    for post in posts:
        user = await users_collection.find_one({"_id": post.get("user_id")}, {"username": 1, "email": 1})
        post["_id"] = str(post["_id"])
        post["user_id"] = str(post.get("user_id", ""))
        post["username"] = user.get("username", "Unknown") if user else "Unknown"
        post["user_email"] = user.get("email", "") if user else ""
        enriched_posts.append(post)
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "posts": enriched_posts
    }


@router.get("/posts/{post_id}/detail")
@require_role(Role.ADMIN)
async def get_post_detail_admin(
    post_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lấy chi tiết bài viết kèm thông tin user, reports và AI analysis."""
    posts_collection = db["anon_posts"]
    users_collection = db["users"]
    reports_collection = db["reports"]
    
    try:
        post = await posts_collection.find_one({"_id": ObjectId(post_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid post_id format")
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get user info
    user = await users_collection.find_one({"_id": post.get("user_id")}, {"username": 1, "email": 1})
    
    # Get reports for this post
    reports = await reports_collection.find({"target_id": post_id}).to_list(length=100)
    for report in reports:
        report["_id"] = str(report["_id"])
    
    post["_id"] = str(post["_id"])
    post["user_id"] = str(post.get("user_id", ""))
    post["username"] = user.get("username", "Unknown") if user else "Unknown"
    post["user_email"] = user.get("email", "") if user else ""
    post["reports"] = reports
    post["report_count"] = len(reports)
    
    return post


@router.put("/posts/{post_id}/status")
@require_role(Role.ADMIN)
async def update_post_status(
    post_id: str,
    status: str = Query(..., description="New status: Approved or Hidden"),
    reason: str = Query(None, description="Reason for status change"),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Cập nhật trạng thái bài viết."""
    if status not in ["Approved", "Hidden", "Blocked", "Pending"]:
        raise HTTPException(status_code=400, detail="Invalid status. Use: Approved, Hidden, Blocked, Pending")
    
    collection = db["anon_posts"]
    
    try:
        result = await collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"moderation_status": status, "status_reason": reason}}
        )
    except:
        raise HTTPException(status_code=400, detail="Invalid post_id format")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"message": f"Post status updated to {status}", "post_id": post_id}


@router.put("/posts/batch-status")
@require_role(Role.ADMIN)
async def batch_update_post_status(
    post_ids: list[str] = Query(..., description="List of post IDs"),
    status: str = Query(..., description="New status: Approved or Hidden"),
    reason: str = Query(None, description="Reason for status change"),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Cập nhật trạng thái nhiều bài viết cùng lúc."""
    if status not in ["Approved", "Hidden", "Blocked", "Pending"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    collection = db["anon_posts"]
    
    try:
        object_ids = [ObjectId(pid) for pid in post_ids]
    except:
        raise HTTPException(status_code=400, detail="Invalid post_id format in list")
    
    result = await collection.update_many(
        {"_id": {"$in": object_ids}},
        {"$set": {"moderation_status": status, "status_reason": reason}}
    )
    
    return {
        "message": f"Updated {result.modified_count} posts to status {status}",
        "modified_count": result.modified_count
    }


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


# --- AI Integration ---
@router.post("/ai/webhook/analysis-result")
@require_role(Role.ADMIN)
async def receive_ai_analysis_result(
    post_id: str = Query(..., description="Post ID"),
    sentiment: str = Query(..., description="Sentiment from AI"),
    risk_level: str = Query(..., description="Risk level from AI"),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Webhook nhận kết quả phân tích từ AI.
    Tự động cập nhật trạng thái bài viết dựa trên risk level.
    """
    collection = db["anon_posts"]
    
    try:
        post = await collection.find_one({"_id": ObjectId(post_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid post_id format")
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Determine action based on risk level
    new_status = "Approved"
    if risk_level in ["high", "critical"]:
        new_status = "Blocked"
    elif risk_level == "medium":
        new_status = "Pending"
    
    await collection.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {
            "ai_sentiment": sentiment,
            "ai_risk_level": risk_level,
            "moderation_status": new_status if post.get("moderation_status") == "Pending" else post.get("moderation_status")
        }}
    )
    
    return {
        "message": "AI analysis result received",
        "post_id": post_id,
        "sentiment": sentiment,
        "risk_level": risk_level,
        "updated_status": new_status
    }


@router.post("/posts/{post_id}/ai-feedback")
@require_role(Role.ADMIN)
async def submit_ai_feedback(
    post_id: str,
    is_correct: bool = Query(..., description="AI prediction is correct?"),
    correct_sentiment: str = Query(None, description="Correct sentiment if AI was wrong"),
    correct_risk_level: str = Query(None, description="Correct risk level if AI was wrong"),
    feedback_note: str = Query(None, description="Additional feedback note"),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Gửi feedback cho AI về kết quả phân tích."""
    collection = db["ai_feedbacks"]
    
    feedback = {
        "post_id": post_id,
        "is_correct": is_correct,
        "correct_sentiment": correct_sentiment,
        "correct_risk_level": correct_risk_level,
        "feedback_note": feedback_note,
        "admin_id": str(current_user["_id"]),
        "created_at": datetime.utcnow()
    }
    
    await collection.insert_one(feedback)
    
    return {"message": "AI feedback submitted", "post_id": post_id}


@router.get("/stats/ai-analysis")
@require_role(Role.ADMIN)
async def get_ai_analysis_stats(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Thống kê sentiment/risk level từ AI."""
    collection = db["anon_posts"]
    
    # Sentiment distribution
    sentiment_stats = await collection.aggregate([
        {"$match": {"ai_sentiment": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$ai_sentiment", "count": {"$sum": 1}}}
    ]).to_list(length=100)
    
    # Risk level distribution
    risk_stats = await collection.aggregate([
        {"$match": {"ai_risk_level": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$ai_risk_level", "count": {"$sum": 1}}}
    ]).to_list(length=100)
    
    # Status distribution
    status_stats = await collection.aggregate([
        {"$group": {"_id": "$moderation_status", "count": {"$sum": 1}}}
    ]).to_list(length=100)
    
    return {
        "sentiment": {item["_id"]: item["count"] for item in sentiment_stats},
        "risk_level": {item["_id"]: item["count"] for item in risk_stats},
        "status": {item["_id"]: item["count"] for item in status_stats}
    }


@router.get("/stats/overview")
@require_role(Role.ADMIN)
async def get_overview_stats(
    period: Optional[Literal["today", "week", "month", "all"]] = Query("today"),
    date: Optional[str] = Query(None, description="Specific date: YYYY-MM-DD"),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Dashboard nâng cao với nhiều thống kê chi tiết."""
    now = datetime.utcnow()
    
    # Calculate date filter
    start_date = None
    if date:
        try:
            specific_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = specific_date
        except:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    elif period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    
    date_filter = {"created_at": {"$gte": start_date}} if start_date else {}
    
    # Aggregate stats
    users_today = await db["users"].count_documents(date_filter)
    posts_today = await db["anon_posts"].count_documents(date_filter)
    comments_today = await db["anon_comments"].count_documents(date_filter)
    reports_today = await db["reports"].count_documents(date_filter)
    
    return {
        "period": period or "all",
        "date": date,
        "stats": {
            "users": users_today,
            "posts": posts_today,
            "comments": comments_today,
            "reports": reports_today
        },
        "generated_at": now.isoformat()
    }


# --- User Violation ---
@router.get("/users/{user_id}/violations")
@require_role(Role.ADMIN)
async def get_user_violations(
    user_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lấy lịch sử vi phạm của user."""
    # Get blocked/hidden posts
    blocked_posts = await db["anon_posts"].find({
        "user_id": ObjectId(user_id),
        "moderation_status": {"$in": ["Blocked", "Hidden"]}
    }).to_list(length=100)
    
    # Get reports against this user
    user_reports = await db["reports"].find({
        "target_user_id": user_id
    }).to_list(length=100)
    
    for post in blocked_posts:
        post["_id"] = str(post["_id"])
        post["user_id"] = str(post.get("user_id", ""))
    
    for report in user_reports:
        report["_id"] = str(report["_id"])
    
    return {
        "user_id": user_id,
        "blocked_posts": blocked_posts,
        "blocked_posts_count": len(blocked_posts),
        "reports_against": user_reports,
        "reports_count": len(user_reports)
    }


# --- Expert Articles Management Extended ---
@router.get("/expert-articles/approved", response_model=list[ExpertArticleResponse])
@require_role(Role.ADMIN)
async def list_approved_expert_articles(
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lấy danh sách bài viết expert đã duyệt."""
    service = ExpertArticleService(db)
    return await service.list_articles_by_status("approved", limit)


@router.get("/expert-articles")
@require_role(Role.ADMIN)
async def list_all_expert_articles(
    status: str = Query(None, description="Filter: pending, approved, rejected"),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lấy danh sách tất cả bài viết expert với filter."""
    service = ExpertArticleService(db)
    if status:
        return await service.list_articles_by_status(status, limit)
    return await service.list_all_articles(limit)
