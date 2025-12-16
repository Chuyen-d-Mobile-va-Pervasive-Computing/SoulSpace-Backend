from datetime import datetime
from app.repositories.report_repository import ReportRepository
from app.models.report_model import Report
from bson import ObjectId, errors
from app.schemas.user.report_schema import AdminReportResponse

class ReportService:
    def __init__(self, db):
        self.db = db
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

    async def list_reports(self, status: str = None) -> list[AdminReportResponse]:
        raw_reports = await self.repo.list(status=status)
        enriched_reports = []
        
        for report in raw_reports:
            # DEBUG: In ra để kiểm tra
            print(f"[DEBUG] Report ID: {report['_id']}")
            print(f"[DEBUG] Target ID: {report['target_id']}, Type: {type(report['target_id'])}")
            
            # 1. Lấy username người báo cáo
            reporter = await self.db["users"].find_one(
                {"_id": report["reporter_id"]}, {"username": 1}
            )
            reporter_username = reporter.get("username", "Unknown") if reporter else "Unknown"

            # 2. Lấy nội dung bị báo cáo - FIX QUAN TRỌNG!
            target_content = "[Content not found]"
            target_author_username = "Unknown"
            
            try:
                # CONVERT string sang ObjectId
                target_object_id = ObjectId(report["target_id"])
                
                if report["target_type"] == "post":
                    target_doc = await self.db["anon_posts"].find_one(
                        {"_id": target_object_id},  # ← DÙNG ObjectId
                        {"content": 1, "user_id": 1, "is_anonymous": 1}
                    )
                    
                    if target_doc:
                        print(f"[DEBUG] Found post: {target_doc.get('content', '')[:50]}")
                        target_content = target_doc.get("content", "")
                        
                        # Xác định author name
                        if target_doc.get("is_anonymous", True):
                            target_author_username = "Anonymous"
                        else:
                            author = await self.db["users"].find_one(
                                {"_id": target_doc["user_id"]}, {"username": 1}
                            )
                            target_author_username = author.get("username", "Unknown") if author else "Unknown"
                
                elif report["target_type"] == "comment":
                    target_doc = await self.db["anon_comments"].find_one(
                        {"_id": target_object_id},
                        {"content": 1, "user_id": 1}
                    )
                    
                    if target_doc:
                        target_content = target_doc.get("content", "")
                        author = await self.db["users"].find_one(
                            {"_id": target_doc["user_id"]}, {"username": 1}
                        )
                        target_author_username = author.get("username", "Unknown") if author else "Unknown"
                        
            except Exception as e:
                print(f"[ERROR] Failed to fetch content for {report['target_id']}: {e}")
                # Fallback: Thử query với string ID
                if report["target_type"] == "post":
                    target_doc = await self.db["anon_posts"].find_one(
                        {"_id": report["target_id"]},  # String fallback
                        {"content": 1}
                    )
                    if target_doc:
                        target_content = target_doc.get("content", "")

            # 3. Tạo response
            enriched_report = AdminReportResponse(
                _id=report["_id"],
                reporter_username=reporter_username,
                target_type=report["target_type"],
                target_id=str(report["target_id"]),
                target_content=target_content,
                target_author_username=target_author_username,
                reason=report["reason"],
                status=report["status"],
                created_at=report.get("created_at")
            )
            enriched_reports.append(enriched_report)
        
        return enriched_reports

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
