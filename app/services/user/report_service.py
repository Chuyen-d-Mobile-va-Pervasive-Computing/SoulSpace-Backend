from datetime import datetime
from app.repositories.report_repository import ReportRepository
from app.models.report_model import Report
from bson import ObjectId

class ReportService:
    def __init__(self, db):
        self.repo = ReportRepository(db)

    async def create_report(self, user_id: str, target_id: str, target_type: str, reason: str):
        report_data = Report(
            reporter_id=ObjectId(user_id),
            target_id=ObjectId(target_id),
            target_type=target_type,
            reason=reason,
            status="pending",
            created_at=datetime.utcnow()
        ).dict(by_alias=True)
        
        return await self.repo.create(report_data)

    async def list_reports(self, status: str = None):
        return await self.repo.list(status=status)
