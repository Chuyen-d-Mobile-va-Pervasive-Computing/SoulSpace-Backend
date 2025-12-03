from fastapi import APIRouter, Depends
from app.schemas.user.anon_comment_schema import AnonCommentCreate, AnonCommentResponse
from app.services.user.anon_comment_service import AnonCommentService
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/anon-comments", tags=["👤 User - Anonymous Comments (Bình luận ẩn danh)"])

@router.post("/", response_model=AnonCommentResponse)
async def create_comment(payload: AnonCommentCreate, db=Depends(get_db), user=Depends(get_current_user)):
    service = AnonCommentService(db)
    comment = await service.create_comment(
        user_id=user["_id"],
        post_id=payload.post_id,
        content=payload.content,
        is_preset=payload.is_preset
    )
    return comment

@router.get("/{post_id}", response_model=list[AnonCommentResponse])
async def list_comments(post_id: str, db=Depends(get_db)):
    service = AnonCommentService(db)
    return await service.comment_repo.list_by_post(post_id)

@router.delete("/{comment_id}")
async def delete_comment(comment_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    service = AnonCommentService(db)
    return await service.delete_comment(comment_id, user["_id"])