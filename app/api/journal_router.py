from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from app.schemas.journal_schema import JournalCreate, JournalResponse
from app.repositories.journal_repository import JournalRepository
from app.services.journal_service import JournalService
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.constants import ICON_SENTIMENT_MAP
from typing import List, Optional
import uuid
import os
from time import time

router = APIRouter(prefix="/journal", tags=["journal"])

def serialize_journal(journal) -> JournalResponse:
    """Serialize Journal model to JournalResponse schema."""
    return JournalResponse(
        id=str(journal.id),
        user_id=str(journal.user_id),
        created_at=journal.created_at,
        emotion_label=journal.emotion_label,
        text_content=journal.text_content,
        voice_note_path=journal.voice_note_path,
        voice_text=journal.voice_text,
        sentiment_label=journal.sentiment_label,
        sentiment_score=journal.sentiment_score,
        tags=journal.tags,
    )

@router.post("/", response_model=JournalResponse)
async def create_journal(
    request: Request,  # Thêm Request để debug và parse form data
    voice_note: UploadFile = File(None),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new journal entry with optional voice note."""
    form_data = await request.form()

    # Tạo instance JournalCreate từ form data
    data = JournalCreate(
        emotion_label=form_data.get("emotion_label"),
        text_content=form_data.get("text_content"),
        voice_note_path=None if not voice_note else "temp_path",  # Gán tạm để xử lý sau
        tags=form_data.getlist("tags") if form_data.get("tags") else None
    )

    file_path: Optional[str] = None
    try:
        # Validate inputs
        if not data.emotion_label:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Emotion label is required")
        if not data.text_content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text content is required")
        if data.emotion_label not in ICON_SENTIMENT_MAP:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid emotion label")
        if data.tags and any(len(tag) > 50 or not tag.strip() for tag in data.tags):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Each tag must be 1-50 characters and non-empty")

        if voice_note:
            file_extension = os.path.splitext(voice_note.filename)[1].lower()
            if file_extension != ".mp3":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only MP3 files are supported")
            file_name = f"{uuid.uuid4()}{file_extension}"
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(await voice_note.read())
            data.voice_note_path = file_path

        try:
            service = JournalService(JournalRepository(db))
            journal = await service.create_journal(str(current_user["_id"]), data)
            if voice_note and os.path.exists(file_path):
                os.remove(file_path)
            return serialize_journal(journal)
        except Exception as e:
            if voice_note and os.path.exists(file_path):
                os.remove(file_path)
            raise
    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create journal: {str(e)}")

@router.get("/", response_model=List[JournalResponse])
async def get_journals(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all journal entries for the authenticated user."""
    try:
        service = JournalService(JournalRepository(db))
        journals = await service.get_user_journals(str(current_user["_id"]))
        return [serialize_journal(j) for j in journals]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch journals: {str(e)}")

@router.post("/test-stt", response_model=dict)
async def test_stt(
    voice_note: UploadFile = File(..., description="Upload an English MP3 file for transcription"),
):
    """Test the Speech-to-Text model with an English MP3 file, returning the transcribed text."""
    file_path = None
    try:
        # Validate file extension
        file_extension = os.path.splitext(voice_note.filename)[1].lower()
        if file_extension != ".mp3":
            raise HTTPException(status_code=400, detail="Only MP3 files are supported")

        # Save to temp file for AssemblyAI
        file_name = f"{uuid.uuid4()}{file_extension}"
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file_name)
        start_time = time()
        with open(file_path, "wb") as f:
            f.write(await voice_note.read())

    # Transcribe using STT service
        service = JournalService(None)
        voice_text = await service.transcribe_audio(open(file_path, "rb").read())
        processing_time = time() - start_time

        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
        return {
            "voice_text": voice_text,
            "processing_time": processing_time,
            "status": "success"
        }
    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process STT: {str(e)}")