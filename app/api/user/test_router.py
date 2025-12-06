from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from app.services.user.test_service import UserTestService, get_user_test_service
from app.services.user.user_test_result_service import UserTestResultService, get_user_test_result_service
from app.core.dependencies import get_current_user
from app.schemas.user.test_schema import UserTestSchema
from app.schemas.user.user_test_result_schema import UserTestResultSchema

router = APIRouter(prefix="/tests", tags=["User - Tests"])

@router.get("", response_model=List[UserTestSchema])
async def get_all_tests(service: UserTestService = Depends(get_user_test_service)):
    return await service.get_all_tests()

@router.get("/{test_code}/questions")
async def get_test_questions(test_code: str, service: UserTestService = Depends(get_user_test_service)):
    return await service.get_test_questions(test_code)

@router.post("/{test_code}/submit", status_code=201)
async def submit_test(test_code: str, payload: dict, service: UserTestResultService = Depends(get_user_test_result_service), user=Depends(get_current_user)):
    return await service.submit_test(user["_id"], test_code, payload["answers"])

@router.get("/result/{result_id}", response_model=UserTestResultSchema)
async def get_result_detail(result_id: str, service: UserTestResultService = Depends(get_user_test_result_service), user=Depends(get_current_user)):
    return await service.get_result_detail(ObjectId(result_id))