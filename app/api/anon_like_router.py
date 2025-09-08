from fastapi import APIRouter, Depends
from app.services.anon_like_service import AnonLikeService
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/anon-likes", tags=["Anonymous Likes"])

@router.post("/{post_id}")
async def like_post(post_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    service = AnonLikeService(db)
    return await service.like_post(user["_id"], post_id)

@router.delete("/{post_id}")
async def unlike_post(post_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    service = AnonLikeService(db)
    return await service.unlike_post(user["_id"], post_id)