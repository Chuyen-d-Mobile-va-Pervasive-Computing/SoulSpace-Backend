from fastapi import APIRouter, Depends
from app.services.user.anon_like_service import AnonLikeService
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/anon-likes", tags=["User - Anonymous Likes (Thích bài viết)"])

@router.post("/{post_id}")
async def like_post(post_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    service = AnonLikeService(db)
    return await service.like_post(user["_id"], post_id)

@router.delete("/{post_id}")
async def unlike_post(post_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    service = AnonLikeService(db)
    return await service.unlike_post(user["_id"], post_id)

@router.get("/{post_id}/users")
async def get_who_liked(post_id: str, db=Depends(get_db)):
    """
    Xem danh sách người đã like bài viết (Expert hoặc User đều dùng được).
    """
    service = AnonLikeService(db)
    return await service.get_users_who_liked(post_id)