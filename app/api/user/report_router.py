from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user.report_schema import ReportCreate, ReportResponse
from app.services.user.report_service import ReportService
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["🚩 User - Reports (Báo cáo)"])

@router.post("/", response_model=ReportResponse)
async def create_report(payload: ReportCreate, db=Depends(get_db), user=Depends(get_current_user)):
    service = ReportService(db)
    return await service.create_report(
        user_id=user["_id"],
        target_id=payload.target_id,
        target_type=payload.target_type,
        reason=payload.reason
    )
