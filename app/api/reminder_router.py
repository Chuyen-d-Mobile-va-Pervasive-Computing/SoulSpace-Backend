from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.reminder_schema import ReminderCreate, ReminderUpdate, ReminderResponse
from app.services.reminder_service import ReminderService
from app.repositories.reminder_repository import ReminderRepository
from app.core.database import get_db
from app.core.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/reminders", tags=["reminders"])

def get_reminder_service(db=Depends(get_db)):
    reminder_repo = ReminderRepository(db)
    return ReminderService(reminder_repo)

class ToggleReminderRequest(BaseModel):
    is_active: bool

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
    """Create a new reminder."""
    return await service.create_reminder(str(current_user["_id"]), reminder_data)

@router.put("/{id}", response_model=ReminderResponse)
async def update_reminder(
    id: str,
    update_data: ReminderUpdate,
    service: ReminderService = Depends(get_reminder_service),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing reminder."""
    return await service.update_reminder(id, str(current_user["_id"]), update_data)

@router.delete("/{id}")
async def delete_reminder(
    id: str,
    service: ReminderService = Depends(get_reminder_service),
    current_user: dict = Depends(get_current_user)
):
    """Delete a reminder."""
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
