from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user.anon_post_schema import AnonPostCreate, AnonPostResponse
from app.services.user.anon_post_service import AnonPostService
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/anon-posts", tags=["👤 User - Anonymous Posts (Bài viết ẩn danh)"])

@router.post("/", response_model=AnonPostResponse)
async def create_post(payload: AnonPostCreate, db=Depends(get_db), user=Depends(get_current_user)):
    service = AnonPostService(db)
    post = await service.create_post(
        user_id=user["_id"], 
        content=payload.content,
        is_anonymous=payload.is_anonymous,
        hashtags=payload.hashtags
    )
    return post

@router.get("/", response_model=list[AnonPostResponse])
async def list_posts(db=Depends(get_db)):
    service = AnonPostService(db)
    return await service.post_repo.list()

@router.delete("/{post_id}")
async def delete_post(post_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    service = AnonPostService(db)
    return await service.delete_post(user["_id"], post_id)