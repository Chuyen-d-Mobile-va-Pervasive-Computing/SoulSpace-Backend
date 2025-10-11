from fastapi import HTTPException, status
from bson import ObjectId
from typing import List, Optional
from app.models.reminder_model import Reminder
from app.core.database import get_db

class ReminderRepository:
    def __init__(self, db):
        self.db = db
        # Create indexes
        self.db.reminders.create_index([("user_id", 1), ("time_of_day", 1)])
        self.db.reminders.create_index([("user_id", 1), ("is_active", 1)])

    async def create(self, reminder: Reminder) -> Reminder:
        """Create a new reminder."""
        try:
            result = await self.db.reminders.insert_one(reminder.dict(by_alias=True))
            reminder.id = result.inserted_id
            return reminder
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create reminder: {str(e)}")

    async def get_by_id(self, reminder_id: str) -> Optional[Reminder]:
        """Get a reminder by ID."""
        try:
            reminder_data = await self.db.reminders.find_one({"_id": ObjectId(reminder_id)})
            if reminder_data:
                # Đảm bảo các trường cần thiết có giá trị mặc định
                reminder_data.setdefault("time_of_day", "")
                reminder_data.setdefault("repeat_type", "once")
                reminder_data.setdefault("repeat_days", [])
            return Reminder(**reminder_data) if reminder_data else None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch reminder: {str(e)}")

    async def get_by_user_id(self, user_id: str) -> List[Reminder]:
        """Get all reminders for a user."""
        try:
            cursor = self.db.reminders.find({"user_id": ObjectId(user_id)})
            reminders = await cursor.to_list(length=100)
            return [Reminder(**{**{"time_of_day": "", "repeat_type": "once", "repeat_days": []}, **reminder}) for reminder in reminders]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch reminders: {str(e)}")

    async def update(self, reminder_id: str, update_data: dict):
        """Update a reminder."""
        try:
            await self.db.reminders.update_one(
                {"_id": ObjectId(reminder_id)},
                {"$set": {k: v for k, v in update_data.items() if v is not None}}
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update reminder: {str(e)}")

    async def delete(self, reminder_id: str):
        """Delete a reminder."""
        try:
            await self.db.reminders.delete_one({"_id": ObjectId(reminder_id)})
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete reminder: {str(e)}")

    async def count_by_user_id(self, user_id: str) -> int:
        """Count reminders for a user."""
        try:
            return await self.db.reminders.count_documents({"user_id": ObjectId(user_id)})
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to count reminders: {str(e)}")