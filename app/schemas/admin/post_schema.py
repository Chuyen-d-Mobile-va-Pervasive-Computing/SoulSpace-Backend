from pydantic import BaseModel, Field

class AdminPostDeleteRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for deletion")