from fastapi import HTTPException, status
from app.models.expert_schedule_model import ExpertSchedule
from bson import ObjectId
from datetime import datetime
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase


class ExpertScheduleRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["expert_schedules"]

    async def get_available_slots(self, expert_id: str, date: str) -> List[ExpertSchedule]:
        """Backward compatibility: Get available slots for a given expert and date (is_booked == False)"""
        try:
            cursor = self.collection.find({
                "expert_id": ObjectId(expert_id),
                "date": date,
                "is_booked": False
            })
            docs = await cursor.to_list(length=None)
            return [ExpertSchedule(**doc) for doc in docs]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch available slots: {str(e)}"
            )

    async def is_slot_conflicting(self, expert_id: str, date: str, start_time: str, end_time: str, exclude_id: str = None):
        query = {
            "expert_id": ObjectId(expert_id),
            "date": date,
            "$or": [
                {"start_time": {"$lt": end_time}, "end_time": {"$gt": start_time}},
                {"end_time": start_time},
                {"start_time": end_time}
            ]
        }
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        count = await self.collection.count_documents(query)
        return count > 0

    async def create_schedule(self, expert_id: str, schedule_data: dict) -> ExpertSchedule:
        if await self.is_slot_conflicting(
            expert_id,
            schedule_data["date"],
            schedule_data["start_time"],
            schedule_data["end_time"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slot overlaps or adjacent to existing schedule"
            )
        schedule_data["expert_id"] = ObjectId(expert_id)
        schedule_data["is_booked"] = False
        result = await self.collection.insert_one(schedule_data)
        created = await self.collection.find_one({"_id": result.inserted_id})
        return ExpertSchedule(**created)

    async def get_schedules_by_month(self, expert_id: str, year_month: str) -> List[ExpertSchedule]:
        try:
            year, month = map(int, year_month.split("-"))
            start_date = f"{year}-{month:02d}-01"
            next_month = datetime(year + (month // 12), ((month % 12) + 1), 1)
            end_date = next_month.strftime("%Y-%m-%d")
        except:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
        cursor = self.collection.find({
            "expert_id": ObjectId(expert_id),
            "date": {"$gte": start_date, "$lt": end_date}
        }).sort([("date", 1), ("start_time", 1)])
        docs = await cursor.to_list(length=None)
        return [ExpertSchedule(**doc) for doc in docs]

    async def get_by_id_and_expert(self, schedule_id: str, expert_id: str) -> ExpertSchedule:
        doc = await self.collection.find_one({
            "_id": ObjectId(schedule_id),
            "expert_id": ObjectId(expert_id)
        })
        if not doc:
            raise HTTPException(status_code=404, detail="Schedule not found or access denied")
        return ExpertSchedule(**doc)

    async def delete_schedule(self, schedule_id: str, expert_id: str) -> bool:
        schedule = await self.get_by_id_and_expert(schedule_id, expert_id)
        if schedule.is_booked:
            raise HTTPException(status_code=400, detail="Cannot delete a booked slot")
        result = await self.collection.delete_one({"_id": ObjectId(schedule_id)})
        return result.deleted_count > 0