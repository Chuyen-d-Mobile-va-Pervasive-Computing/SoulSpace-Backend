from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user_model import User
from app.core.dependencies import get_current_user
from app.schemas.user.test_schema import TestResponseSchema
from app.schemas.admin.test_schema import TestUpdatePayloadSchema, TestCreateSchema 
from app.services.admin.test_service import (
    AdminTestService, 
    get_admin_test_service, 
    TestNotFoundError, 
    TestAlreadyExistsError
)
from typing import List
from app.core.dependencies import get_current_admin
from app.services.admin.test_service import AdminTestService, get_admin_test_service
from app.schemas.admin.test_schema import AdminTestListSchema, AdminTestQuestionSchema
router = APIRouter(prefix="/tests", tags=["Admin Tests"])

@router.get(
    "",
    response_model=List[AdminTestListSchema],
    summary="Admin - Get all available tests (not soft deleted)"
)
async def admin_get_all_tests(
    test_service: AdminTestService = Depends(get_admin_test_service),
    current_admin = Depends(get_current_admin)
):
    try:
        tests = await test_service.get_all_active_tests()
        return tests
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get(
    "/{test_code}/questions",
    response_model=List[AdminTestQuestionSchema],
    summary="Admin - Get questions for a test"
)
async def admin_get_test_questions(
    test_code: str,
    test_service: AdminTestService = Depends(get_admin_test_service),
    current_admin = Depends(get_current_admin)
):
    try:
        questions = await test_service.get_questions_by_test_code(test_code)
        return questions
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post(
    "",
    response_model=TestResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new test"
)
async def admin_create_test(
    payload: TestCreateSchema,
    test_service: AdminTestService = Depends(get_admin_test_service),
    current_user: User = Depends(get_current_user)
):
    try:
        return await test_service.create_test(payload, current_user["_id"])
    except TestAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put(
    "/{test_code}",
    response_model=TestResponseSchema,
    summary="Update test info and questions"
)
async def admin_update_test(
    test_code: str,
    payload: TestUpdatePayloadSchema,
    test_service: AdminTestService = Depends(get_admin_test_service),
    current_user: User = Depends(get_current_user) 
):
    try:
        return await test_service.update_test_structure(test_code, payload, current_user["_id"])
    except TestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/{test_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a test"
)
async def admin_delete_test(
    test_code: str,
    test_service: AdminTestService = Depends(get_admin_test_service),
    current_user: User = Depends(get_current_user)
):
    try:
        await test_service.delete_test(test_code, current_user["_id"])
    except TestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))