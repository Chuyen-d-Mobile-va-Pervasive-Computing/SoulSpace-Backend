from app.models.report_model import Report
from bson import ObjectId

class ReportRepository:
    def __init__(self, db):
        self.collection = db["reports"]

    async def create(self, report_data: dict):
        result = await self.collection.insert_one(report_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def list(self, status: str = None):
        query = {}
        if status:
            query["status"] = status
        return await self.collection.find(query).sort("created_at", -1).to_list(length=1000)

    async def get_by_id(self, report_id: str):
        """Get a report by its ID - handles both ObjectId and string formats."""
        doc = None
        # Try ObjectId query first
        try:
            doc = await self.collection.find_one({"_id": ObjectId(report_id)})
        except Exception:
            doc = None
        
        # Fallback to plain string _id (legacy data)
        if not doc:
            doc = await self.collection.find_one({"_id": report_id})
        
        return doc

    async def update_status(self, report_id: str, status: str):
        """Update the status of a report - handles both ObjectId and string formats."""
        result = None
        # Try ObjectId query first
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(report_id)},
                {"$set": {"status": status}},
                return_document=True
            )
        except Exception:
            result = None
        
        # Fallback to plain string _id (legacy data)
        if not result:
            result = await self.collection.find_one_and_update(
                {"_id": report_id},
                {"$set": {"status": status}},
                return_document=True
            )
        
        return result

