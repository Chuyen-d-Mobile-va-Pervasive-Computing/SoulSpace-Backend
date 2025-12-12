from bson import ObjectId
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.utils.pyobjectid import PyObjectId


class AdminTestOptionSchema(BaseModel):
    option_id: Optional[str] = Field(None, description="Auto-generated if not provided")
    option_text: str = Field(..., max_length=200)
    score: int = Field(..., ge=0)
    option_order: Optional[int] = Field(None, ge=1, description="Auto-generated if not provided")

    class Config:
        schema_extra = {
            "example": {
                "option_text": "Never",
                "score": 0
                # option_order không cần gửi
            }
        }


class AdminTestQuestionSchema(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    question_text: str = Field(..., max_length=500)
    question_order: Optional[int] = Field(None, ge=1, description="Auto-generated if not provided")
    options: List[AdminTestOptionSchema] = Field(..., min_items=2)

    @validator("options")
    def min_two_options(cls, v):
        if len(v) < 2:
            raise ValueError("Each question must have at least 2 options")
        return v

    class Config:
        schema_extra = {
            "example": {
                "question_text": "How often do you feel sad?",
                "options": [
                    {"option_text": "Not at all", "score": 0},
                    {"option_text": "Several days", "score": 1},
                    {"option_text": "More than half the days", "score": 2},
                    {"option_text": "Nearly every day", "score": 3}
                ]
            }
        }


class AdminTestCreateSchema(BaseModel):
    test_code: str = Field(..., max_length=50, description="Must be unique")
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    image_url: Optional[str] = None
    severe_threshold: int = Field(..., gt=0)
    expert_recommendation: str = Field(..., max_length=1000)
    questions: List[AdminTestQuestionSchema] = Field(..., min_items=1)

    class Config:
        schema_extra = {
            "example": {
                "test_code": "phq9-2025",
                "title": "PHQ-9 Depression Test",
                "description": "Standard 9-question depression screening tool",
                "image_url": "https://example.com/phq9.png",
                "severe_threshold": 15,
                "expert_recommendation": "You should consult a mental health professional",
                "questions": [
                    {
                        "question_text": "Little interest or pleasure in doing things?",
                        "options": [
                            {"option_text": "Not at all", "score": 0},
                            {"option_text": "Several days", "score": 1},
                            {"option_text": "More than half the days", "score": 2},
                            {"option_text": "Nearly every day", "score": 3}
                        ]
                    }
                ]
            }
        }


class AdminTestUpdateSchema(BaseModel):
    test_code: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    severe_threshold: Optional[int] = Field(None, gt=0)
    expert_recommendation: Optional[str] = None
    questions: Optional[List[AdminTestQuestionSchema]] = None

    class Config:
        schema_extra = {
            "example": {
                "title": "PHQ-9 Updated lần 4",
                "questions": [
                    {
                        "_id": "693bc0e3a87b6569aa0ec369",
                        "question_text": "Do you feel tired? (v4)",
                        "options": [
                            {"option_id": "693bc0e3a87b6569aa0ec367", "option_text": "Not at all (v4)", "score": 0},
                            {"option_id": "693bc0e3a87b6569aa0ec368", "option_text": "Several days (v4)", "score": 1}
                        ]
                    },
                    {
                        "question_text": "New question - Trouble concentrating?",
                        "options": [
                            {"option_text": "Not at all", "score": 0},
                            {"option_text": "Several days", "score": 1},
                            {"option_text": "More than half", "score": 2},
                            {"option_text": "Nearly every day", "score": 3}
                        ]
                    }
                ]
            }
        }


class AdminTestResponseSchema(BaseModel):
    id: PyObjectId = Field(alias="_id")
    test_code: str
    title: str
    description: str
    image_url: Optional[str]
    severe_threshold: int
    expert_recommendation: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    created_by: Optional[PyObjectId]
    updated_by: Optional[PyObjectId]
    is_deleted: bool
    questions: List[AdminTestQuestionSchema] = []

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}