# app/api/admin/test_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from app.services.admin.test_service import AdminTestService, get_admin_test_service
from app.core.dependencies import get_current_admin
from app.schemas.admin.test_schema import (
    AdminTestResponseSchema,
    AdminTestCreateSchema,
    AdminTestUpdateSchema,
)
from app.utils.convert import convert_objectid_to_str

router = APIRouter(prefix="/admin/tests", tags=["Admin - Tests"])

@router.get("", response_model=List[AdminTestResponseSchema])
async def get_all_tests(
    service: AdminTestService = Depends(get_admin_test_service),
    admin=Depends(get_current_admin)
):
    """Get all tests with questions"""
    tests = await service.get_all_tests()
    result = []
    for t in tests:
        t = convert_objectid_to_str(t)
        if "updated_by" not in t:
            t["updated_by"] = None
        result.append(t)
    return result


@router.get("/{test_id}", response_model=AdminTestResponseSchema)
async def get_test_detail(
    test_id: str,
    service: AdminTestService = Depends(get_admin_test_service),
    admin=Depends(get_current_admin)
):
    """Get test detail by ID"""
    try:
        test = await service.get_test_detail(ObjectId(test_id))
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        obj = convert_objectid_to_str(test)
        if "updated_by" not in obj:
            obj["updated_by"] = None
        return obj
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid test_id format")


@router.post("", status_code=201, response_model=dict)
async def create_test(
    payload: AdminTestCreateSchema,
    service: AdminTestService = Depends(get_admin_test_service),
    admin=Depends(get_current_admin)
):
    """Create new test with questions"""
    try:
        test_data = payload.dict()
        questions_data = test_data.pop("questions")
        test_id = await service.create_test(test_data, questions_data, str(admin["_id"]))
        return {"message": "Test created successfully", "test_id": test_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create test")


@router.put("/{test_id}", response_model=dict)
async def update_test(
    test_id: str,
    payload: AdminTestUpdateSchema,
    service: AdminTestService = Depends(get_admin_test_service),
    admin=Depends(get_current_admin)
):
    try:
        # QUAN TRỌNG: Dùng by_alias=True để giữ nguyên "_id"
        success = await service.update_test(
            ObjectId(test_id),
            payload.dict(exclude_unset=True, by_alias=True) 
        )
        if not success:
            raise HTTPException(status_code=404, detail="Test not found or no changes")
        return {"message": "Test updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Update failed")


@router.delete("/{test_id}", response_model=dict)
async def delete_test(
    test_id: str,
    service: AdminTestService = Depends(get_admin_test_service),
    admin=Depends(get_current_admin)
):
    """Soft delete test and all its questions"""
    try:
        success = await service.soft_delete_test(ObjectId(test_id))
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        return {"message": "Test deleted successfully (soft delete)"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid test_id format")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Delete failed")