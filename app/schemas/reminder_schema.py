from pydantic import BaseModel, Field, validator
from typing import Optional, List
from app.utils.pyobjectid import PyObjectId

class ReminderCreate(BaseModel):
    title: str = Field(..., max_length=30)
    message: str = Field(..., max_length=200)
    time_of_day: str  # "HH:mm"
    repeat_type: str = "once"  # Default to "once"
    repeat_days: Optional[List[int]] = None  # 0-6, only for "custom"

    @validator("time_of_day")
    def validate_time_of_day(cls, v):
        try:
            hours, minutes = map(int, v.split(":"))
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError
            return v
        except (ValueError, AttributeError):
            raise ValueError("time_of_day must be in HH:mm format (00:00-23:59)")

    @validator("repeat_type")
    def validate_repeat_type(cls, v):
        if v not in ["once", "daily", "custom"]:
            raise ValueError("repeat_type must be 'once', 'daily', or 'custom'")
        return v

    @validator("repeat_days")
    def validate_repeat_days(cls, v, values):
        if values.get("repeat_type") == "custom":
            if v is None or not v or not all(isinstance(d, int) and 0 <= d <= 6 for d in v):
                raise ValueError("repeat_days must be a non-empty list of integers 0-6 when repeat_type is 'custom'")
            if len(v) != len(set(v)):  # Check for duplicates
                raise ValueError("repeat_days must not contain duplicate values")
        elif v is not None:  # Cho phép [] hoặc null cho "once" và "daily"
            raise ValueError("repeat_days should be empty, null, or omitted for 'once' or 'daily'")
        return v

    class Config:
        schema_extra = {
            "example": {
                "title": "Drink Water",
                "message": "Drink a glass of water at 2 PM",
                "time_of_day": "14:00",
                "repeat_type": "once",
                "repeat_days": None
            }
        }

class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=30)
    message: Optional[str] = Field(None, max_length=200)
    time_of_day: Optional[str] = None
    repeat_type: Optional[str] = None
    repeat_days: Optional[List[int]] = None
    is_active: Optional[bool] = None
    

    class Config:
        schema_extra = {
            "example": {
                "title": "Updated Drink Water",
                "time_of_day": "15:00",
                "repeat_type": "daily",
                "is_active": False
            }
        }

class ReminderResponse(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    user_id: PyObjectId
    title: str
    message: str
    time_of_day: str
    repeat_type: str
    repeat_days: Optional[List[int]]
    is_active: bool
    

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}