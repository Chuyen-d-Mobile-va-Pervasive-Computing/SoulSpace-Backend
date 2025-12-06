from pydantic import BaseModel
from typing import Optional

class CloudinaryUploadRequestSchema(BaseModel):
    file: bytes
    filename: str
    content_type: str

class CloudinaryUploadResponseSchema(BaseModel):
    url: str
    public_id: Optional[str] = None
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None
