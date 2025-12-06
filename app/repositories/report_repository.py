from app.models.report_model import Report
from bson import ObjectId

class ReportRepository:
    def __init__(self, db):
        self.collection = db["reports"]

    async def create(self, report_data: dict):
        result = await self.collection.insert_one(report_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def list(self):
        return await self.collection.find().to_list(length=1000)
