# app/api/user/test_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from app.services.user.test_service import UserTestService, get_user_test_service
from app.services.user.user_test_result_service import UserTestResultService, get_user_test_result_service, TestNotFoundError, InvalidOptionError
from app.core.dependencies import get_current_user
from app.schemas.user.test_schema import UserTestSchema
from app.schemas.user.user_test_result_schema import UserTestResultSchema, SubmitTestPayloadSchema
from app.utils.convert import convert_objectid_to_str

router = APIRouter(prefix="/tests", tags=["User - Tests"])

@router.get("", response_model=List[UserTestSchema])
async def get_all_tests(service: UserTestService = Depends(get_user_test_service)):
    return await service.get_all_tests()

@router.get("/{test_code}/questions")
async def get_test_questions(test_code: str, service: UserTestService = Depends(get_user_test_service)):
    return await service.get_test_questions(test_code)

@router.post("/{test_code}/progress", response_model=UserTestResultSchema, status_code=status.HTTP_200_OK)
async def save_test_progress(
    test_code: str,
    payload: SubmitTestPayloadSchema,
    service: UserTestResultService = Depends(get_user_test_result_service),
    user=Depends(get_current_user)
):
    """Lưu hoặc cập nhật tiến trình làm bài test. Gửi lên các câu trả lời đã làm."""
    try:
        result = await service.save_test_progress(user["_id"], test_code, payload)
        return convert_objectid_to_str(result)
    except TestNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOptionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.post("/{test_code}/submit", status_code=201)
async def submit_test(test_code: str, payload: SubmitTestPayloadSchema, service: UserTestResultService = Depends(get_user_test_result_service), user=Depends(get_current_user)):
    result = await service.submit_test(user["_id"], test_code, payload)
    return convert_objectid_to_str(result)

@router.get("/result/{result_id}", response_model=UserTestResultSchema)
async def get_result_detail(result_id: str, service: UserTestResultService = Depends(get_user_test_result_service), user=Depends(get_current_user)):
    result = await service.get_result_detail(ObjectId(result_id))
    return convert_objectid_to_str(result)