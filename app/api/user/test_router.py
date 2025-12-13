from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.utils.pyobjectid import PyObjectId
from app.models.user_model import User
from app.core.dependencies import get_current_user

from app.schemas.user.test_schema import (
    TestQuestionResponseSchema, 
    TestWithProgressResponseSchema
)
from app.services.user.test_service import (
    UserTestService,
    get_user_test_service,
    TestNotFoundError
)
from app.schemas.user.user_test_result_schema import (
    SubmitTestPayloadSchema, 
    UserTestResultResponseSchema,  
    CompletedTestSummarySchema, 
    UserTestResultDetailSchema,
    TestProgressDetailSchema
)
from app.services.user.user_test_result_service import (
    UserTestResultService, get_user_test_result_service,
    ResultNotFoundError, NotOwnerOfResultError,
    AnswerCountMismatchError, InvalidOptionError
)

router = APIRouter(prefix="/tests", tags=["User Tests"])

@router.get(
    "",
    response_model=List[TestWithProgressResponseSchema],
    summary="Get all available tests" 
)
async def get_all_available_tests_with_progress(
    test_service: UserTestService = Depends(get_user_test_service),
    current_user: User = Depends(get_current_user) 
):
    try:
        return await test_service.get_all_tests_with_user_progress(current_user["_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{test_code}/questions",
    response_model=List[TestQuestionResponseSchema],
    summary="Get questions for a test"
)
async def get_questions_for_a_test(
    test_code: str,
    test_service: UserTestService = Depends(get_user_test_service)
):
    try:
        return await test_service.get_questions_for_test(test_code)
    except TestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/{test_code}/progress",
    response_model=UserTestResultResponseSchema,
    summary="Save draft progress"
)
async def save_test_progress(
    test_code: str,
    payload: SubmitTestPayloadSchema,
    service: UserTestResultService = Depends(get_user_test_result_service),
    current_user: dict = Depends(get_current_user)
):
    try:
        return await service.save_test_progress(current_user["_id"], test_code, payload)
    except TestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidOptionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/{test_code}/submit",
    response_model=UserTestResultResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Submit completed test"
)
async def submit_completed_test(
    test_code: str,
    payload: SubmitTestPayloadSchema,
    service: UserTestResultService = Depends(get_user_test_result_service),
    current_user: dict = Depends(get_current_user)
):
    try:
        return await service.submit_completed_test(current_user["_id"], test_code, payload)
    except TestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (AnswerCountMismatchError, InvalidOptionError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{test_code}/progress",
    response_model=TestProgressDetailSchema,
    summary="Get current in-progress draft (Resume test)"
)
async def get_test_progress(
    test_code: str,
    service: UserTestResultService = Depends(get_user_test_result_service),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy thông tin bài làm đang dang dở để User làm tiếp.
    Nếu trả về 404 nghĩa là chưa có bài làm dở -> Frontend cho User làm mới từ đầu.
    """
    try:
        draft = await service.get_current_progress(current_user["_id"], test_code)
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="No in-progress test found for this user."
            )
        return draft
    except TestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get(
    "/completed",
    response_model=List[CompletedTestSummarySchema],
    summary="Get completed tests history"
)
async def get_completed_tests_summary(
    service: UserTestResultService = Depends(get_user_test_result_service),
    current_user: User = Depends(get_current_user)
):
    try:
        return await service.get_user_completed_tests_summary(current_user["_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/result/{result_id}",
    response_model=UserTestResultDetailSchema,
    summary="Get result details"
)
async def get_test_result_details(
    result_id: PyObjectId,
    service: UserTestResultService = Depends(get_user_test_result_service),
    current_user: User = Depends(get_current_user)
):
    try:
        return await service.get_result_details(result_id, current_user["_id"])
    except ResultNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotOwnerOfResultError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))