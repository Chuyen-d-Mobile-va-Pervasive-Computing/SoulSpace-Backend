from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.dependencies import get_current_user
from app.schemas.user.user_tree_schema import (
    UserTreeResponseSchema, 
    WaterTreePayloadSchema,
    PositiveActionResponseSchema
)
from app.services.user.user_tree_service import (
    UserTreeService,
    get_user_tree_service,
    PositiveActionNotFoundError,
    AlreadyWateredTodayError,
    DatabaseOperationError
)

router = APIRouter(prefix="/tree", tags=["👤 User - Mental Tree (Cây tinh thần)"])

@router.get(
    "/status",
    response_model=UserTreeResponseSchema,
    summary="Get user's mental tree status"
)
async def get_my_tree_status(
    service: UserTreeService = Depends(get_user_tree_service),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user["_id"]
        return await service.get_user_tree_status(user_id) 
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không xác định: {e}"
        )

@router.post(
    "/nourish",
    response_model=UserTreeResponseSchema,
    summary="Nourish (Water) the mental tree with positive thoughts"
)
async def nourish_my_tree(
    payload: WaterTreePayloadSchema,
    service: UserTreeService = Depends(get_user_tree_service),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user["_id"]
        updated_tree = await service.nourish_tree(user_id, payload.action_id, payload.positive_thoughts)
        return updated_tree
    except AlreadyWateredTodayError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PositiveActionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (DatabaseOperationError, Exception) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get(
    "/positive-actions",
    response_model=List[PositiveActionResponseSchema],
    summary="Get list of available positive actions"
)
async def get_positive_actions(
    service: UserTreeService = Depends(get_user_tree_service)
):
    """
    Lấy danh sách các hành động tích cực mẫu (ví dụ: "Viết 3 điều biết ơn")
    để frontend có thể gửi action_id chính xác khi nourish cây.
    """
    try:
        return await service.get_all_positive_actions()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể tải danh sách hành động: {e}"
        )