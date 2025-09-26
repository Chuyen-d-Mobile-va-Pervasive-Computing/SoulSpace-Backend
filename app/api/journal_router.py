from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from app.schemas.journal_schema import JournalCreate, JournalResponse, TagSchema
from app.repositories.journal_repository import JournalRepository
from app.services.journal_service import JournalService
from app.core.database import get_db
from app.core.dependencies import get_current_user
from typing import List, Optional
import logging
import uuid
import os
from time import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/journal", tags=["journal"])

def serialize_journal(journal) -> JournalResponse:
    """Serialize Journal model to JournalResponse schema."""
    return JournalResponse(
        id=str(journal.id),
        user_id=str(journal.user_id),
        created_at=journal.created_at,
        emotion_label=journal.emotion_label,
        emotion_emoji=journal.emotion_emoji,
        text_content=journal.text_content,
        voice_note_path=journal.voice_note_path,
        voice_text=journal.voice_text,
        sentiment_label=journal.sentiment_label,
        sentiment_score=journal.sentiment_score,
        tags=journal.tags,
    )

@router.post("/", response_model=JournalResponse)
async def create_journal(
    data: JournalCreate = Depends(),
    voice_note: UploadFile = File(None),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new journal entry with optional voice note."""
    try:
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
            logger.info(f"Saved voice note temporarily to: {data.voice_note_path}")
        try:
            service = JournalService(JournalRepository(db))
            journal = await service.create_journal(str(current_user["_id"]), data)
            if voice_note and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Removed temporary file: {file_path}")
            return serialize_journal(journal)
        except Exception as e:
            if voice_note and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Removed temporary file on error: {file_path}")
            raise
    except Exception as e:
        logger.error(f"Failed to create journal: {str(e)}")
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
        logger.error(f"Failed to fetch journals: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch journals: {str(e)}")

@router.post("/test-stt", response_model=dict)
async def test_stt(
    voice_note: UploadFile = File(..., description="Upload an English MP3 file for transcription"),
):
    """Test the Speech-to-Text model with an English MP3 file, returning the transcribed text."""
    try:
        # Validate file extension
        file_extension = os.path.splitext(voice_note.filename)[1].lower()
        if file_extension != ".mp3":
            raise HTTPException(status_code=400, detail="Only MP3 files are supported")

        # Generate unique filename and save to temp directory
        file_name = f"{uuid.uuid4()}{file_extension}"
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file_name)
        start_time = time()
        with open(file_path, "wb") as f:
            f.write(await voice_note.read())
        logger.info(f"Saved audio file to: {file_path}")

        # Transcribe using STT service (no database or user dependency needed)
        service = JournalService(None)  # Pass None since no DB is needed for STT test
        voice_text = service.transcribe_audio(file_path)
        processing_time = time() - start_time

        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Removed temporary file: {file_path}")

        # Return result with processing time
        logger.info(f"STT result: {voice_text}, Processing time: {processing_time:.2f}s")
        return {
            "voice_text": voice_text,
            "processing_time": processing_time,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Failed to test STT: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Removed temporary file on error: {file_path}")
        raise HTTPException(status_code=500, detail=f"Failed to process STT: {str(e)}")