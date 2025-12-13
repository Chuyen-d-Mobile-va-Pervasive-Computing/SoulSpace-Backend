"""
Expert role API endpoints.
These endpoints are for expert-only operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Security, UploadFile, File, Form
from fastapi.security import HTTPBearer
from app.core.dependencies import get_current_user, get_expert_service
from app.core.permissions import Role, require_role
from app.schemas.expert.expert_article_schema import ExpertArticleCreate, ExpertArticleResponse
from app.services.expert.expert_article_service import ExpertArticleService
from app.services.common.cloudinary_service import CloudinaryService
from app.core.database import get_db

# Security scheme for Swagger UI lock icon
security = HTTPBearer()

router = APIRouter(
    prefix="/expert", 
    tags=["👨‍⚕️ Expert - Consultation (Chuyên gia)"],
    dependencies=[Security(security)]  # Hiển thị lock icon cho Swagger UI
)


@router.get("/health")
async def expert_health_check():
    """
    Health check endpoint for expert routes.
    This is a placeholder for future expert functionality.
    """
    return {
        "status": "healthy",
        "role": "expert",
        "message": "Expert routes are ready for implementation"
    }


@router.get("/info")
@require_role(Role.EXPERT)
async def expert_info(current_user: dict = Depends(get_current_user)):
    """
    Get expert-specific information.
    This endpoint requires expert role.
    """
    return {
        "message": "Expert access granted",
        "user": current_user.get("username", "unknown"),
        "role": current_user.get("role", "unknown")
    }


@router.get("/my-profile")
@require_role(Role.EXPERT)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    service = Depends(get_expert_service)
):
    """
    Lấy thông tin profile và profile_id của expert hiện tại.
    Expert cần profile_id này để theo dõi trạng thái duyệt.
    """
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


@router.post("/articles", response_model=ExpertArticleResponse)
@require_role(Role.EXPERT)
async def create_article(payload: ExpertArticleCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = ExpertArticleService(db)
    return await service.create_article(
        expert_id=str(current_user["_id"]),  # Convert to string
        title=payload.title,
        content=payload.content,
        image_url=payload.image_url
    )


@router.post("/articles/with-image", response_model=ExpertArticleResponse)
@require_role(Role.EXPERT)
async def create_article_with_image(
    title: str = Form(..., description="Tiêu đề bài viết"),
    content: str = Form(..., description="Nội dung bài viết"),
    hashtags: str = Form("", description="Danh sách hashtags, phân cách bằng dấu phẩy"),
    image: UploadFile = File(None, description="Ảnh đính kèm (optional)"),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    cloudinary_service: CloudinaryService = Depends()
):
    """
    Tạo bài viết chuyên gia với ảnh đính kèm.
    
    - **title**: Tiêu đề bài viết (bắt buộc)
    - **content**: Nội dung bài viết (bắt buộc)
    - **hashtags**: Danh sách hashtags, phân cách bằng dấu phẩy (ví dụ: "health,mental")
    - **image**: File ảnh (optional)
    """
    image_url = None
    if image:
        try:
            result = await cloudinary_service.upload_avatar(image)
            image_url = result["url"]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to upload image: {str(e)}")
    
    service = ExpertArticleService(db)
    return await service.create_article(
        expert_id=str(current_user["_id"]),
        title=title,
        content=content,
        image_url=image_url
    )


@router.get("/articles", response_model=list[ExpertArticleResponse])
@require_role(Role.EXPERT)
async def list_my_articles(db=Depends(get_db), current_user=Depends(get_current_user)):
    service = ExpertArticleService(db)
    return await service.get_expert_articles(str(current_user["_id"]))  # Convert to string
