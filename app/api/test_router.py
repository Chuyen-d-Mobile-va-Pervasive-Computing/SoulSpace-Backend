from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas.test_schema import TestResponseSchema, TestQuestionResponseSchema
from app.services.test_service import (
    TestService, 
    get_test_service,
    TestNotFoundError,
    TestDataIntegrityError,
    DatabaseOperationError
)

router = APIRouter(prefix="/tests", tags=["Psychological Tests"])

@router.get(
    "",
    response_model=List[TestResponseSchema],
    summary="Get a list of all available tests"
)
async def get_all_available_tests(
    test_service: TestService = Depends(get_test_service)
):
    try:
        return await test_service.get_all_tests()
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