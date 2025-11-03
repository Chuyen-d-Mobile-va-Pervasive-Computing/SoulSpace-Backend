from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.utils.pyobjectid import PyObjectId

from app.schemas.test_schema import TestResponseSchema, TestQuestionResponseSchema, TestWithProgressResponseSchema
from app.services.test_service import (
    TestService,
    get_test_service,
    TestNotFoundError,
    TestDataIntegrityError,
    DatabaseOperationError
)
from app.core.dependencies import get_current_user
from app.models.user_model import User

from app.schemas.test_schema import TestResponseSchema, TestQuestionResponseSchema
from app.schemas.user_test_result_schema import SubmitTestPayloadSchema, UserTestResultResponseSchema  ,  CompletedTestSummarySchema, UserTestResultDetailSchema
from app.services.test_service import get_test_service
from app.services.user_test_result_service import (
    UserTestResultService, get_user_test_result_service,
    TestNotFoundError, ResultNotFoundError, NotOwnerOfResultError,
    TestAlreadyCompletedError, AnswerCountMismatchError, InvalidOptionError,

)


router = APIRouter(prefix="/tests", tags=["Psychological Tests"])

@router.get(
    "",
    response_model=List[TestWithProgressResponseSchema],
    summary="Get all tests with user's completion progress" 
)
async def get_all_available_tests_with_progress(
    test_service: TestService = Depends(get_test_service),
    current_user: User = Depends(get_current_user) 
):
    try:
        return await test_service.get_all_tests_with_user_progress(current_user["_id"])
    except DatabaseOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server Error: Could not retrieve tests from the database. Original error: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred. Details: {e}"
        )

@router.get(
    "/{test_code}/questions",
    response_model=List[TestQuestionResponseSchema],
    summary="Get all questions for a specific test"
)
async def get_questions_for_a_test(
    test_code: str,
    test_service: TestService = Depends(get_test_service)
):

    try:
        return await test_service.get_questions_for_test(test_code)
    except TestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TestDataIntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server Configuration Error: {e}"
        )
    except DatabaseOperationError as e:
        # Dịch lỗi "database" thành lỗi 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server Error: A database issue occurred. Original error: {e}"
        )
    except Exception as e:
        # Bắt các lỗi không mong muốn khác
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred. Details: {e}"
        )


@router.post(
    "/{test_code}/progress",
    response_model=UserTestResultResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Save user's test progress (draft)"
)
async def save_test_progress(
    test_code: str,
    payload: SubmitTestPayloadSchema,
    service: UserTestResultService = Depends(get_user_test_result_service),
    current_user: dict = Depends(get_current_user)
):
    """Lưu hoặc cập nhật tiến trình làm bài test. Gửi lên các câu trả lời đã làm."""
    try:
        return await service.save_test_progress(current_user["_id"], test_code, payload)
    except TestNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOptionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.post(
    "/{test_code}/submit",
    response_model=UserTestResultResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a completed test (handles both new and draft submissions)"
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (AnswerCountMismatchError, InvalidOptionError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.get(
    "/completed",
    response_model=List[CompletedTestSummarySchema],
    summary="Get summary of all completed tests for the current user"
)
async def get_completed_tests_summary(
    service: UserTestResultService = Depends(get_user_test_result_service),
    current_user: User = Depends(get_current_user)
):
    try:
        return await service.get_user_completed_tests_summary(current_user["_id"])
    except DatabaseOperationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.get(
    "/result/{result_id}",
    response_model=UserTestResultDetailSchema,
    summary="Get detailed results of a specific test attempt"
)
async def get_test_result_details(
    result_id: PyObjectId,
    service: UserTestResultService = Depends(get_user_test_result_service),
    current_user: User = Depends(get_current_user)
):
    try:
        return await service.get_result_details(result_id, current_user["_id"])
    except ResultNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotOwnerOfResultError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")