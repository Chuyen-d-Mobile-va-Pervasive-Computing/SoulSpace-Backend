from fastapi import HTTPException, status
from bson import ObjectId
from typing import List
from app.models.reminder_model import Reminder
from app.schemas.reminder_schema import ReminderCreate, ReminderUpdate, ReminderResponse
from app.repositories.reminder_repository import ReminderRepository

class ReminderService:
    def __init__(self, reminder_repo: ReminderRepository):
        """Initialize ReminderService with a reminder repository."""
        self.reminder_repo = reminder_repo

    async def create_reminder(self, user_id: str, reminder_data: ReminderCreate) -> ReminderResponse:
        """Create a new reminder for a user.

        Args:
            user_id: ID of the authenticated user.
            reminder_data: Data for the new reminder.

        Raises:
            HTTPException: If user exceeds 10 reminders or database error occurs.

        Returns:
            ReminderResponse: Created reminder details.
        """
        if await self.reminder_repo.count_by_user_id(user_id) >= 10:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 10 reminders allowed per user")

        reminder = Reminder(
            user_id=ObjectId(user_id),
            title=reminder_data.title,
            message=reminder_data.message,
            remind_time=reminder_data.remind_time,
            is_custom=reminder_data.is_custom
        )
        try:
            created_reminder = await self.reminder_repo.create(reminder)
            return ReminderResponse(
                id=created_reminder.id,
                user_id=created_reminder.user_id,
                title=created_reminder.title,
                message=created_reminder.message,
                remind_time=created_reminder.remind_time.isoformat(),
                is_active=created_reminder.is_active,
                is_custom=created_reminder.is_custom
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create reminder: {str(e)}")

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
                remind_time=reminder.remind_time.isoformat(),
                is_active=reminder.is_active,
                is_custom=reminder.is_custom
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

        await self.reminder_repo.update(reminder_id, update_data.dict(exclude_unset=True))
        updated_reminder = await self.reminder_repo.get_by_id(reminder_id)
        return ReminderResponse(
            id=updated_reminder.id,
            user_id=updated_reminder.user_id,
            title=updated_reminder.title,
            message=updated_reminder.message,
            remind_time=updated_reminder.remind_time.isoformat(),
            is_active=updated_reminder.is_active,
            is_custom=updated_reminder.is_custom
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
