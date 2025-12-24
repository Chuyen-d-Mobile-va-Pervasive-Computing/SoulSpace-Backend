"""
Expert role API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Security, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer
from typing import List, Optional, Union

from app.core.dependencies import get_current_user, get_expert_service, get_feed_service, get_current_user_optional
from app.core.permissions import Role, require_role
from app.schemas.expert.expert_article_schema import ExpertArticleCreate, ExpertArticleResponse
from app.schemas.common.feed_schema import FeedItemResponse
from app.services.expert.expert_article_service import ExpertArticleService
from app.services.common.feed_service import FeedService
from app.services.common.cloudinary_service import CloudinaryService
from app.core.database import get_db

security = HTTPBearer()

router = APIRouter(
    prefix="/expert", 
    tags=["Expert - Forum (Chuyên gia)"],
    dependencies=[Security(security)]
)

@router.get("/my-profile")
@require_role(Role.EXPERT)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    service = Depends(get_expert_service)
):
    user_id = str(current_user["_id"])
    profile = await service.get_expert_by_user_id(user_id)
    if not profile:
        raise HTTPException(
            status_code=404, 
            detail="Expert profile not found. Please complete your profile first."
        )
    return {
        "profile_id": str(profile.id),
        "user_id": user_id,
        "full_name": profile.full_name,
        "phone": profile.phone,
        "date_of_birth": profile.date_of_birth,
        "bio": profile.bio,
        "avatar_url": profile.avatar_url,
        "status": profile.status,
        "years_of_experience": profile.years_of_experience,
        "clinic_name": profile.clinic_name,
        "clinic_address": profile.clinic_address,
        "certificate_url": profile.certificate_url,
        "created_at": profile.created_at,
        "approval_date": profile.approval_date,
        "approved_by": str(profile.approved_by) if profile.approved_by else None
    }

# --- ARTICLE FEATURES ---
@router.post("/articles", response_model=ExpertArticleResponse)
@require_role(Role.EXPERT)
async def create_article_with_image(
    title: str = Form(..., description="Tiêu đề bài viết"),
    content: str = Form(..., description="Nội dung bài viết"),
    hashtags: str = Form("", description="Danh sách hashtags, phân cách bằng dấu phẩy"),
    image: Union[UploadFile, str, None] = File(None, description="Ảnh đính kèm hoặc URL ảnh"),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    cloudinary_service: CloudinaryService = Depends()
):
    image_url = None
    
    # DEBUG LOG
    print(f"DEBUG: Type: {type(image)}")

    # CASE 1: Người dùng gửi File (UploadFile từ starlette hoặc fastapi)
    # SỬA Ở ĐÂY: Dùng hasattr để kiểm tra thay vì isinstance
    if image is not None and hasattr(image, "filename"):
        # Ép kiểu thủ công để IDE không báo lỗi (nếu cần), hoặc cứ dùng trực tiếp
        file_obj = image 
        if file_obj.filename: # Kiểm tra tên file không rỗng
            try:
                result = await cloudinary_service.upload_post_image(file_obj)
                image_url = result["url"]
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Image upload failed: {str(e)}")
    
    # CASE 2: Người dùng gửi String (URL ảnh có sẵn)
    elif isinstance(image, str):
        if image.strip(): 
            image_url = image

    # Xử lý hashtags
    hashtag_list = [h.strip() for h in hashtags.split(",") if h.strip()] if hashtags else []

    # Get Expert Profile
    from app.repositories.expert_repository import ExpertRepository
    expert_repo = ExpertRepository(db)
    profile = await expert_repo.get_by_user_id(str(current_user["_id"]))
    if not profile:
        raise HTTPException(status_code=403, detail="Expert profile not found")

    service = ExpertArticleService(db)
    return await service.create_article(
        expert_id=str(profile.id),
        title=title,
        content=content,
        image_url=image_url,
        hashtags=hashtag_list
    )

@router.get("/articles/feed", response_model=List[FeedItemResponse])
async def get_mixed_feed(
    limit: int = Query(20, ge=1, le=100),
    service: FeedService = Depends(get_feed_service),
    current_user: Optional[dict] = Depends(get_current_user_optional) # Allow both logged-in and anon users
):
    """
    Lấy Newsfeed tổng hợp:
    - Bao gồm: Bài viết User (Approved) + Bài PR Expert (Approved).
    - Sắp xếp: Mới nhất lên đầu.
    - User/Expert đều xem được.
    """
    user_id = str(current_user["_id"]) if current_user else None
    return await service.get_mixed_feed(limit=limit, current_user_id=user_id)


@router.get("/articles/my-articles", response_model=List[ExpertArticleResponse])
@require_role(Role.EXPERT)
async def list_my_articles(db=Depends(get_db), current_user=Depends(get_current_user)):
    """Lấy danh sách bài viết của chính Expert (để quản lý)"""
    from app.repositories.expert_repository import ExpertRepository
    expert_repo = ExpertRepository(db)
    profile = await expert_repo.get_by_user_id(str(current_user["_id"]))
    if not profile:
        raise HTTPException(status_code=403, detail="Profile not found")

    service = ExpertArticleService(db)
    return await service.get_expert_articles(str(profile.id))

@router.delete("/articles/{article_id}")
@require_role(Role.EXPERT)
async def delete_article(
    article_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Xóa bài viết PR (Chỉ được xóa khi trạng thái là Pending)"""
    from app.repositories.expert_repository import ExpertRepository
    expert_repo = ExpertRepository(db)
    profile = await expert_repo.get_by_user_id(str(current_user["_id"]))
    if not profile:
        raise HTTPException(status_code=403, detail="Profile not found")

    service = ExpertArticleService(db)
    success = await service.delete_article(article_id, str(profile.id))
    if success:
        return {"message": "Article deleted successfully"}
    raise HTTPException(status_code=400, detail="Failed to delete. Article might not exist or is not pending.")

@router.get("/articles/{article_id}", response_model=ExpertArticleResponse)
async def get_article_detail(
    article_id: str,
    db=Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Xem chi tiết bài viết (bao gồm số like, comment)"""
    service = ExpertArticleService(db)
    # Service cần gọi Repo.get_by_id và truyền user_id vào để check like
    # Vì service ở trên chưa sửa, ta sửa ở đây hoặc update service
    # Logic chuẩn là Service gọi Repo.
    
    # Cập nhật tạm thời service call tại đây để pass current_user_id
    from app.repositories.expert_article_repository import ExpertArticleRepository
    repo = ExpertArticleRepository(db)
    
    user_id = str(current_user["_id"]) if current_user else None
    article = await repo.get_by_id(article_id, current_user_id=user_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article