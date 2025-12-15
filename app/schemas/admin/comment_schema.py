# app/schemas/admin/comment_schema.py
from pydantic import BaseModel, Field

class AdminCommentDeleteRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for deletion")