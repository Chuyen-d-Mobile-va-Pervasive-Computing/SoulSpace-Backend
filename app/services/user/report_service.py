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

    async def resolve_report(self, report_id: str, action: str):
        """
        Resolve a report with the given action.
        Actions:
        - delete_content: Delete the reported content (post/comment)
        - warn_user: Warn the user who created the content (mark as resolved)
        - dismiss: Dismiss the report without action (mark as rejected)
        """
        # Validate action
        valid_actions = ["delete_content", "warn_user", "dismiss"]
        if action not in valid_actions:
            raise ValueError(f"Invalid action. Must be one of: {valid_actions}")
        
        # Get the report
        report = await self.repo.get_by_id(report_id)
        if not report:
            raise ValueError("Report not found")
        
        # Determine new status based on action
        if action == "dismiss":
            new_status = "rejected"
        else:
            new_status = "resolved"
        
        # Update report status
        updated_report = await self.repo.update_status(report_id, new_status)
        
        return {
            "message": f"Report {new_status} successfully",
            "report_id": report_id,
            "action": action,
            "status": new_status
        }
