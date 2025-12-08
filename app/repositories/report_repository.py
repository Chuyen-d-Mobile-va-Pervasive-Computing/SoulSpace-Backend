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
