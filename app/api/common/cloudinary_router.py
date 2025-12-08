from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.common.cloudinary_service import CloudinaryService
from app.schemas.common.cloudinary_schema import CloudinaryUploadResponseSchema
from app.schemas.expert.expert_schema import FileUploadResponse
from app.core.dependencies import get_current_admin, get_current_expert

router = APIRouter(prefix="/api/v1/upload", tags=["Cloudinary Upload"])


# Admin upload image for test
@router.post("/admin/test-image", response_model=CloudinaryUploadResponseSchema)
async def upload_test_image(file: UploadFile = File(...), service: CloudinaryService = Depends()):
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

# Expert upload avatar
@router.post("/expert/avatar", response_model=FileUploadResponse)
async def upload_expert_avatar(file: UploadFile = File(...), service: CloudinaryService = Depends()):
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

# Expert upload certificate
@router.post("/expert/certificate", response_model=FileUploadResponse)
async def upload_expert_certificate(file: UploadFile = File(...), service: CloudinaryService = Depends()):
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
