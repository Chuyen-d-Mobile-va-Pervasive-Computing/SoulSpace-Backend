from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.user.reminder_schema import ReminderCreate, ReminderUpdate, ReminderResponse
from app.services.user.reminder_service import ReminderService
from app.repositories.reminder_repository import ReminderRepository
from app.core.database import get_db
from app.core.dependencies import get_current_user
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

router = APIRouter(prefix="/reminders", tags=["👤 User - Reminders (Nhắc nhở)"])

# Initialize scheduler
scheduler = AsyncIOScheduler()
scheduler.start()

def get_reminder_service(db=Depends(get_db)):
    reminder_repo = ReminderRepository(db)
    return ReminderService(reminder_repo)

class ToggleReminderRequest(BaseModel):
    is_active: bool

def schedule_reminder(reminder: dict, remind_at: datetime):
    """Schedule a one-time reminder."""
    scheduler.add_job(
        lambda: None,
        "date",
        run_date=remind_at,
        id=str(reminder["id"])
    )

def schedule_repeating_reminder(reminder: dict):
    """Schedule a repeating reminder (daily or custom)."""
    if reminder["repeat_type"] == "daily":
        scheduler.add_job(
            lambda: None,
            "cron",
            hour=int(reminder["time_of_day"].split(":")[0]),
            minute=int(reminder["time_of_day"].split(":")[1]),
            id=str(reminder["id"])
        )
    elif reminder["repeat_type"] == "custom" and reminder["repeat_days"]:
        for day in reminder["repeat_days"]:
            scheduler.add_job(
                lambda d=day: None,
                "cron",
                day_of_week=f"{day}",
                hour=int(reminder["time_of_day"].split(":")[0]),
                minute=int(reminder["time_of_day"].split(":")[1]),
                id=f"{reminder['id']}_{day}"
            )
    pass

@router.get("/", response_model=List[ReminderResponse])
async def get_reminders(
    service: ReminderService = Depends(get_reminder_service),
    current_user: dict = Depends(get_current_user)
):
    """Get all reminders for the authenticated user."""
    return await service.get_reminders(str(current_user["_id"]))

@router.post("/", response_model=ReminderResponse)
async def create_reminder(
    reminder_data: ReminderCreate,
    service: ReminderService = Depends(get_reminder_service),
    current_user: dict = Depends(get_current_user)
):
    """Create a new reminder with scheduling."""
    reminder = await service.create_reminder(str(current_user["_id"]), reminder_data)
    reminder_dict = reminder.dict()
    if reminder.repeat_type == "once":
        now = datetime.utcnow()
        hours, minutes = map(int, reminder.time_of_day.split(":"))
        remind_at = datetime.combine(now.date(), datetime.min.time().replace(hour=hours, minute=minutes, second=0))
        if remind_at < now:
            remind_at += timedelta(days=1)
        schedule_reminder(reminder_dict, remind_at)
    elif reminder.repeat_type in ["daily", "custom"]:
        schedule_repeating_reminder(reminder_dict)
    return reminder

@router.put("/{id}", response_model=ReminderResponse)
async def update_reminder(
    id: str,
    update_data: ReminderUpdate,
    service: ReminderService = Depends(get_reminder_service),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing reminder and reschedule if needed."""
    updated_reminder = await service.update_reminder(id, str(current_user["_id"]), update_data)
    reminder_dict = updated_reminder.dict()

    # Remove existing jobs
    for job in scheduler.get_jobs():
        if str(updated_reminder.id) in job.id:
            job.remove()

    # Reschedule
    if updated_reminder.repeat_type == "once":
        now = datetime.utcnow()
        hours, minutes = map(int, updated_reminder.time_of_day.split(":"))
        remind_at = datetime.combine(now.date(), datetime.min.time().replace(hour=hours, minute=minutes, second=0))
        if remind_at < now:
            remind_at += timedelta(days=1)
        schedule_reminder(reminder_dict, remind_at)
    elif updated_reminder.repeat_type in ["daily", "custom"]:
        schedule_repeating_reminder(reminder_dict)

    return updated_reminder

@router.delete("/{id}")
async def delete_reminder(
    id: str,
    service: ReminderService = Depends(get_reminder_service),
    current_user: dict = Depends(get_current_user)
):
    """Delete a reminder and remove its schedule."""
    reminder = await service.get_reminders(str(current_user["_id"]))
    for r in reminder:
        if str(r.id) == id:
            for job in scheduler.get_jobs():
                if str(r.id) in job.id:
                    job.remove()
    await service.delete_reminder(id, str(current_user["_id"]))
    return {"message": "Reminder deleted successfully"}

@router.post("/toggle/{id}")
async def toggle_reminder(
    id: str,
    toggle_data: ToggleReminderRequest,
    service: ReminderService = Depends(get_reminder_service),
    current_user: dict = Depends(get_current_user)
):
    """Toggle the active status of a reminder."""
    await service.toggle_reminder(id, str(current_user["_id"]), toggle_data.is_active)
    return {"message": f"Reminder {'activated' if toggle_data.is_active else 'deactivated'} successfully"}