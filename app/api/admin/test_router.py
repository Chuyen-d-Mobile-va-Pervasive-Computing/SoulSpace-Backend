from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from app.services.admin.test_service import AdminTestService
from app.services.admin.test_question_service import AdminTestQuestionService
from app.core.dependencies import get_current_admin
from app.schemas.admin.test_schema import AdminTestSchema

router = APIRouter(prefix="/admin/tests", tags=["Admin - Tests"])

from app.services.admin.test_service import AdminTestService, get_admin_test_service

@router.get("", response_model=List[AdminTestSchema])
async def get_all_tests(service: AdminTestService = Depends(get_admin_test_service), admin=Depends(get_current_admin)):
    return await service.get_all_tests()

@router.get("/{test_id}", response_model=AdminTestSchema)
async def get_test_detail(test_id: str, service: AdminTestService = Depends(get_admin_test_service), admin=Depends(get_current_admin)):
    test = await service.get_test_detail(ObjectId(test_id))
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

@router.post("", status_code=201)
async def create_test(test_data: dict, service: AdminTestService = Depends(get_admin_test_service), admin=Depends(get_current_admin)):
    # admin là dict user lấy từ token, thường có _id
    user_id = str(admin["_id"]) if "_id" in admin else None
    return await service.create_test(test_data["test"], test_data["questions"], user_id)

@router.put("/{test_id}")
async def update_test(test_id: str, update_data: dict, service: AdminTestService = Depends(get_admin_test_service), admin=Depends(get_current_admin)):
    return await service.update_test(ObjectId(test_id), update_data)

@router.delete("/{test_id}")
async def delete_test(test_id: str, service: AdminTestService = Depends(get_admin_test_service), admin=Depends(get_current_admin)):
    return await service.soft_delete_test(ObjectId(test_id))
