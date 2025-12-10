from pydantic import BaseModel, Field, validator
from typing import List
from datetime import datetime, timedelta
import re

class ExpertScheduleCreate(BaseModel):
    date: str = Field(..., example="2025-12-20")
    start_time: str = Field(..., example="09:00")
    end_time: str = Field(..., example="10:00")

    @validator("date")
    def validate_date(cls, v):
        try:
            dt = datetime.strptime(v, "%Y-%m-%d")
            datetime(dt.year, dt.month, dt.day)
            return v
        except ValueError:
            raise ValueError("Invalid or non-existent date (e.g. 2025-02-30)")

    @validator("start_time", "end_time")
    def validate_time(cls, v):
        if not re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", v):
            raise ValueError("Invalid time format. Use HH:MM (24h)")
        return v

    @validator("end_time")
    def validate_exact_one_hour_and_no_overnight(cls, end_time, values):
        start_time = values.get("start_time")
        if not start_time:
            return end_time
        try:
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            if end_dt <= start_dt:
                raise ValueError("End time must be after start time (no overnight slots)")
            if (end_dt - start_dt) != timedelta(hours=1):
                raise ValueError("Slot must be exactly 1 hour")
            return end_time
        except Exception as e:
            raise ValueError(f"Time validation error: {str(e)}")

    @validator("start_time")
    def validate_not_in_past(cls, start_time, values):
        date_str = values.get("date")
        if not date_str:
            return start_time
        try:
            slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            now = datetime.now()
            today = now.date()
            if slot_date < today:
                raise ValueError("Cannot create slot in the past")
            if slot_date == today:
                slot_start = datetime.strptime(start_time, "%H:%M").time()
                if slot_start <= now.time():
                    raise ValueError("Cannot create slot at or before current time today")
        except Exception as e:
            raise ValueError(f"Slot time validation error: {str(e)}")
        return start_time

class ExpertScheduleResponse(BaseModel):
    schedule_id: str
    date: str
    start_time: str
    end_time: str
    is_booked: bool = False

class ExpertScheduleListResponse(BaseModel):
    data: List[ExpertScheduleResponse]
