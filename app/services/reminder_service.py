from fastapi import HTTPException, status
from bson import ObjectId
from typing import List
from app.models.reminder_model import Reminder
from app.schemas.reminder_schema import ReminderCreate, ReminderUpdate, ReminderResponse
from app.repositories.reminder_repository import ReminderRepository
from datetime import datetime, timedelta
# logging removed per user request

class ReminderService:
    def __init__(self, reminder_repo: ReminderRepository):
        """Initialize ReminderService with a reminder repository."""
        self.reminder_repo = reminder_repo

    async def create_reminder(self, user_id: str, reminder_data: ReminderCreate) -> ReminderResponse:
        """Create a new reminder for a user with calculated start time for 'once'.

        Args:
            user_id: ID of the authenticated user.
            reminder_data: Data for the new reminder.

        Raises:
            HTTPException: If user exceeds 10 reminders or validation fails.

        Returns:
            ReminderResponse: Created reminder details.
        """
        if await self.reminder_repo.count_by_user_id(user_id) >= 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 reminders allowed per user",
            )

        # Calculate remind_at for "once" type
        if reminder_data.repeat_type == "once":
            now = datetime.utcnow()
            try:
                hours, minutes = map(int, reminder_data.time_of_day.split(":"))
                remind_at = datetime.combine(
                    now.date(),
                    datetime.min.time().replace(
                        hour=hours, minute=minutes, second=0, microsecond=0
                    ),
                )
                if remind_at < now:
                    remind_at += timedelta(days=1)
            except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid time_of_day format, use HH:mm",
                    )

        try:
            user_obj_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user_id format",
            )

        reminder = Reminder(
            user_id=user_obj_id,
            title=reminder_data.title,
            message=reminder_data.message,
            time_of_day=reminder_data.time_of_day,
            repeat_type=reminder_data.repeat_type,
            repeat_days=reminder_data.repeat_days,
        )
        try:
            created_reminder = await self.reminder_repo.create(reminder)
            return ReminderResponse(
                id=str(created_reminder.id),
                user_id=str(created_reminder.user_id),
                title=created_reminder.title,
                message=created_reminder.message,
                time_of_day=created_reminder.time_of_day,
                repeat_type=created_reminder.repeat_type,
                repeat_days=created_reminder.repeat_days,
                is_active=created_reminder.is_active,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create reminder: {str(e)}",
            )

    async def get_reminders(self, user_id: str) -> List[ReminderResponse]:
        """Get all reminders for a user.

        Args:
            user_id: ID of the authenticated user.

        Returns:
            List[ReminderResponse]: List of reminders.
        """
        reminders = await self.reminder_repo.get_by_user_id(user_id)
        return [
            ReminderResponse(
                id=reminder.id,
                user_id=reminder.user_id,
                title=reminder.title,
                message=reminder.message,
                time_of_day=reminder.time_of_day or "",  # Fallback nếu thiếu
                repeat_type=reminder.repeat_type or "once",  # Fallback nếu thiếu
                repeat_days=reminder.repeat_days or [],
                is_active=reminder.is_active,
                
            ) for reminder in reminders
        ]

    async def update_reminder(self, reminder_id: str, user_id: str, update_data: ReminderUpdate) -> ReminderResponse:
        """Update an existing reminder.

        Args:
            reminder_id: ID of the reminder to update.
            user_id: ID of the authenticated user.
            update_data: Data to update the reminder.

        Raises:
            HTTPException: If reminder not found or user unauthorized.

        Returns:
            ReminderResponse: Updated reminder details.
        """
        reminder = await self.reminder_repo.get_by_id(reminder_id)
        if not reminder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
        if str(reminder.user_id) != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to update this reminder")

        # Validate updated repeat_days if repeat_type changes to "custom"
        if update_data.repeat_type == "custom" and (update_data.repeat_days is None or not update_data.repeat_days):
            raise HTTPException(status_code=400, detail="repeat_days is required for custom repeat_type")

        await self.reminder_repo.update(reminder_id, update_data.dict(exclude_unset=True))
        updated_reminder = await self.reminder_repo.get_by_id(reminder_id)
        return ReminderResponse(
            id=updated_reminder.id,
            user_id=updated_reminder.user_id,
            title=updated_reminder.title,
            message=updated_reminder.message,
            time_of_day=updated_reminder.time_of_day or "",
            repeat_type=updated_reminder.repeat_type or "once",
            repeat_days=updated_reminder.repeat_days or [],
            is_active=updated_reminder.is_active,
            
        )

    async def delete_reminder(self, reminder_id: str, user_id: str):
        """Delete a reminder.

        Args:
            reminder_id: ID of the reminder to delete.
            user_id: ID of the authenticated user.

        Raises:
            HTTPException: If reminder not found or user unauthorized.
        """
        reminder = await self.reminder_repo.get_by_id(reminder_id)
        if not reminder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
        if str(reminder.user_id) != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to delete this reminder")

        await self.reminder_repo.delete(reminder_id)

    async def toggle_reminder(self, reminder_id: str, user_id: str, is_active: bool):
        """Toggle the active status of a reminder.

        Args:
            reminder_id: ID of the reminder to toggle.
            user_id: ID of the authenticated user.
            is_active: New active status.

        Raises:
            HTTPException: If reminder not found or user unauthorized.
        """
        reminder = await self.reminder_repo.get_by_id(reminder_id)
        if not reminder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
        if str(reminder.user_id) != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to toggle this reminder")

        await self.reminder_repo.update(reminder_id, {"is_active": is_active})