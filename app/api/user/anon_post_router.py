from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from typing import Optional, List
from app.schemas.user.anon_post_schema import AnonPostCreate, AnonPostResponse
from app.services.user.anon_post_service import AnonPostService
from app.services.common.cloudinary_service import CloudinaryService
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional

router = APIRouter(prefix="/anon-posts", tags=["👤 User - Posts (Bài viết cộng đồng)"])


@router.post("/", response_model=AnonPostResponse)
async def create_post(
    content: str = Form(..., description="Nội dung bài viết"),
    is_anonymous: bool = Form(True, description="True = ẩn danh, False = hiển thị tên"),
    hashtags: str = Form("", description="Danh sách hashtags, phân cách bằng dấu phẩy (ví dụ: 'sharing,public')"),
    image: UploadFile = File(None, description="Ảnh đính kèm (optional)"),
    db=Depends(get_db),
    user=Depends(get_current_user),
    cloudinary_service: CloudinaryService = Depends()
):
    """
    Tạo bài viết mới (có thể đính kèm ảnh).
    
    - **content**: Nội dung bài viết (bắt buộc)
    - **is_anonymous**: True = ẩn danh, False = hiển thị tên (mặc định: True)
    - **hashtags**: Danh sách hashtags, phân cách bằng dấu phẩy
    - **image**: File ảnh đính kèm (optional)
    
    AI Toxic Detection sẽ tự động phân tích nội dung.
    """
    # Upload image if provided
    image_url = None
    if image and image.filename:
        try:
            result = await cloudinary_service.upload_avatar(image)
            image_url = result["url"]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to upload image: {str(e)}")
    
    # Parse hashtags from comma-separated string
    hashtag_list = [h.strip() for h in hashtags.split(",") if h.strip()] if hashtags else []
    
    service = AnonPostService(db)
    post = await service.create_post(
        user_id=user["_id"], 
        content=content,
        is_anonymous=is_anonymous,
        hashtags=hashtag_list,
        image_url=image_url
    )
    return post


@router.get("/", response_model=list[AnonPostResponse])
async def list_posts(
    limit: int = Query(default=20, ge=1, le=100, description="Số lượng bài viết tối đa"),
    db=Depends(get_db),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Lấy danh sách bài viết cộng đồng (đã được duyệt).
    
    - Nếu đã đăng nhập: Hiển thị is_liked, is_owner
    - Nếu chưa đăng nhập: Vẫn xem được nhưng không có is_liked, is_owner
    """
    service = AnonPostService(db)
    current_user_id = str(user["_id"]) if user else None
    return await service.list_posts(limit=limit, current_user_id=current_user_id)


@router.get("/my-posts", response_model=list[AnonPostResponse])
async def get_my_posts(
    limit: int = Query(default=50, ge=1, le=100),
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Lấy tất cả bài viết của mình (bao gồm cả Pending và Blocked).
    Chỉ user đã đăng nhập mới có thể xem.
    """
    service = AnonPostService(db)
    return await service.get_my_posts(user_id=str(user["_id"]), limit=limit)


@router.get("/{post_id}", response_model=AnonPostResponse)
async def get_post_detail(
    post_id: str,
    db=Depends(get_db),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Lấy chi tiết một bài viết.
    """
    service = AnonPostService(db)
    current_user_id = str(user["_id"]) if user else None
    return await service.get_post_detail(post_id=post_id, current_user_id=current_user_id)


@router.delete("/{post_id}")
async def delete_post(
    post_id: str, 
    db=Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    Xóa bài viết của mình.
    Chỉ chủ sở hữu mới có thể xóa.
    """
    service = AnonPostService(db)
    return await service.delete_post(user["_id"], post_id)