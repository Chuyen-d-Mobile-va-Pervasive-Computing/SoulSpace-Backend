import asyncio
import logging
from io import BytesIO
from typing import Dict

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudinaryService:
    """Upload files to Cloudinary with proper async handling"""
    
    def __init__(self):
        try:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET
            )
            logger.info(f"✓ Cloudinary initialized")
        except Exception as e:
            logger.error(f"✗ Cloudinary init failed: {str(e)}")
            raise
    
    async def upload_avatar(self, file: UploadFile) -> Dict:
        """Upload avatar to Cloudinary"""
        
        # Validate MIME type
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid image format. Only JPG/PNG allowed.",
                headers={"X-Error-Code": "E012"}
            )
        
        # Read file
        content = await file.read()
        
        # Validate size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > 2:
            raise HTTPException(
                status_code=413,
                detail=f"Image exceeds 2MB (received {size_mb:.2f}MB)",
                headers={"X-Error-Code": "E013"}
            )
        
        # Validate image (prevent malicious)
        try:
            image = Image.open(BytesIO(content))
            image.verify()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or corrupted image: {str(e)}",
                headers={"X-Error-Code": "E012"}
            )
        
        # Upload (run in executor because cloudinary SDK is sync)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: cloudinary.uploader.upload(
                content,
                folder="soulspace/experts/avatars",
                resource_type="image",
                transformation=[
                    {"width": 500, "height": 500, "crop": "fill"},
                    {"quality": "auto"},
                    {"fetch_format": "auto"}
                ]
            )
        )
        
        logger.info(f"✓ Avatar uploaded: {result['public_id']}")
        
        if "secure_url" not in result:
            logger.error(f"Cloudinary upload missing secure_url: {result}")
            raise HTTPException(
                status_code=500,
                detail=f"Upload failed: {result}",
                headers={"X-Error-Code": "E013"}
            )
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "format": result["format"],
            "width": result.get("width"),
            "height": result.get("height"),
            "size": result.get("bytes")
        }
    
    async def upload_certificate(self, file: UploadFile) -> Dict:
        """Upload certificate to Cloudinary"""
        
        # Validate MIME type
        allowed = ["image/jpeg", "image/png", "application/pdf"]
        if file.content_type not in allowed:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Allowed: JPG/PNG/PDF",
                headers={"X-Error-Code": "E012"}
            )
        
        # Read file
        content = await file.read()
        
        # Validate size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > 5:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds 5MB (received {size_mb:.2f}MB)",
                headers={"X-Error-Code": "E013"}
            )
        
        # Validate PDF magic bytes
        if file.content_type == "application/pdf" and not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file",
                headers={"X-Error-Code": "E012"}
            )
        
        # Validate images
        if file.content_type in ["image/jpeg", "image/png"]:
            try:
                image = Image.open(BytesIO(content))
                image.verify()
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image: {str(e)}",
                    headers={"X-Error-Code": "E012"}
                )
        
        # Upload
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: cloudinary.uploader.upload(
                content,
                folder="soulspace/experts/certificates",
                resource_type="auto"
            )
        )
        
        logger.info(f"✓ Certificate uploaded: {result['public_id']}")
        
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "format": result["format"],
            "size": result.get("bytes")
        }
    
    async def delete_file(self, public_id: str) -> bool:
        """Delete file from Cloudinary"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: cloudinary.uploader.destroy(public_id)
            )
            
            if result.get("result") == "ok":
                logger.info(f"✓ Deleted: {public_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"✗ Delete failed: {str(e)}")
            return False

    async def upload_post_image(self, file: UploadFile) -> Dict:
        """
        Upload ảnh cho bài viết (Article/Post).
        - Cho phép: JPG, PNG, WEBP, JPEG.
        - Max size: 5MB.
        - Không crop cứng, giữ nguyên tỉ lệ.
        """
        
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
        if file.content_type not in allowed_types:
            # Fallback check extension nếu content-type header bị sai
            if not any(file.filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image format. Allowed: JPG, PNG, WEBP. Received: {file.content_type}",
                )
        
        # 2. Read file
        await file.seek(0) 
        content = await file.read()
        
        # 3. Validate size (5MB cho bài viết)
        size_mb = len(content) / (1024 * 1024)
        if size_mb > 5:
            raise HTTPException(
                status_code=413,
                detail=f"Image exceeds 5MB limit (received {size_mb:.2f}MB)",
            )
        
        # 4. Upload
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: cloudinary.uploader.upload(
                    content,
                    folder="soulspace/articles",  # Lưu vào folder riêng
                    resource_type="image",
                    # Không dùng transformation crop vuông 500x500 như avatar
                    transformation=[
                        {"quality": "auto"},
                        {"fetch_format": "auto"}
                    ]
                )
            )
            
            logger.info(f"✓ Article image uploaded: {result.get('public_id')}")
            
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "format": result["format"],
                "width": result.get("width"),
                "height": result.get("height")
            }
        except Exception as e:
            logger.error(f"Cloudinary upload error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")