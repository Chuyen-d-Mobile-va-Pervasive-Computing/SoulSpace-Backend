from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.common.cloudinary_service import CloudinaryService
from app.schemas.common.cloudinary_schema import CloudinaryUploadResponseSchema
from app.schemas.expert.expert_schema import FileUploadResponse
from app.core.dependencies import get_current_admin, get_current_expert, get_current_user

router = APIRouter(prefix="/upload", tags=["☁️ Cloudinary Upload"])


# ============================================
# PUBLIC UPLOADS (No Auth Required)
# For Expert Registration Flow
# ============================================

@router.post("/public/avatar", response_model=CloudinaryUploadResponseSchema)
async def upload_avatar_public(
    file: UploadFile = File(...), 
    service: CloudinaryService = Depends()
):
    """
    Upload avatar CÔNG KHAI (không cần đăng nhập).
    Dùng trong quá trình đăng ký Expert (Phase 2 - Complete Profile).
    
    Lưu ý: Endpoint này public, nên có thể bị abuse. 
    Trong production nên thêm rate limiting.
    """
    try:
        result = await service.upload_avatar(file)
        return CloudinaryUploadResponseSchema(
            url=result["url"],
            public_id=result.get("public_id"),
            format=result.get("format"),
            width=result.get("width"),
            height=result.get("height"),
            size=result.get("size")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/public/certificate", response_model=CloudinaryUploadResponseSchema)
async def upload_certificate_public(
    file: UploadFile = File(...), 
    service: CloudinaryService = Depends()
):
    """
    Upload chứng chỉ CÔNG KHAI (không cần đăng nhập).
    Dùng trong quá trình đăng ký Expert (Phase 2 - Complete Profile).
    
    Hỗ trợ: PDF, PNG, JPEG
    """
    try:
        result = await service.upload_certificate(file)
        return CloudinaryUploadResponseSchema(
            url=result["url"],
            public_id=result.get("public_id"),
            format=result.get("format"),
            width=result.get("width"),
            height=result.get("height"),
            size=result.get("size")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AUTHENTICATED UPLOADS
# ============================================

# User upload avatar (any logged in user)
@router.post("/user/avatar", response_model=CloudinaryUploadResponseSchema)
async def upload_user_avatar(
    file: UploadFile = File(...), 
    service: CloudinaryService = Depends(), 
    user=Depends(get_current_user)
):
    """
    Upload avatar cho user đã đăng nhập.
    Trả về URL để dùng với API update-avatar hoặc update-profile.
    """
    try:
        result = await service.upload_avatar(file)
        return CloudinaryUploadResponseSchema(
            url=result["url"],
            public_id=result.get("public_id"),
            format=result.get("format"),
            width=result.get("width"),
            height=result.get("height"),
            size=result.get("size")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin upload image for test
@router.post("/admin/test-image", response_model=CloudinaryUploadResponseSchema)
async def upload_test_image(
    file: UploadFile = File(...), 
    service: CloudinaryService = Depends(), 
    admin=Depends(get_current_admin)
):
    """Upload ảnh cho bài test (Admin only)."""
    try:
        result = await service.upload_avatar(file)
        return CloudinaryUploadResponseSchema(
            url=result["url"],
            public_id=result.get("public_id"),
            format=result.get("format"),
            width=result.get("width"),
            height=result.get("height"),
            size=result.get("size")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Expert upload avatar (for already logged-in experts)
@router.post("/expert/avatar", response_model=FileUploadResponse)
async def upload_expert_avatar(
    file: UploadFile = File(...), 
    service: CloudinaryService = Depends(), 
    expert=Depends(get_current_expert)
):
    """Upload avatar cho Expert đã đăng nhập."""
    try:
        result = await service.upload_avatar(file)
        return FileUploadResponse(
            url=result["url"],
            public_id=result.get("public_id"),
            format=result.get("format"),
            width=result.get("width"),
            height=result.get("height"),
            size=result.get("size")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Expert upload certificate (for already logged-in experts)
@router.post("/expert/certificate", response_model=FileUploadResponse)
async def upload_expert_certificate(
    file: UploadFile = File(...), 
    service: CloudinaryService = Depends(), 
    expert=Depends(get_current_expert)
):
    """Upload chứng chỉ cho Expert đã đăng nhập."""
    try:
        result = await service.upload_certificate(file)
        return FileUploadResponse(
            url=result["url"],
            public_id=result.get("public_id"),
            format=result.get("format"),
            size=result.get("size")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


