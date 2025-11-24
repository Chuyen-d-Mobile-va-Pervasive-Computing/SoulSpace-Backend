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
    request: Request,
    audio: UploadFile = File(None, description="Optional audio recording (.mp3 or .m4a)"),  # FE gửi field 'audio'
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new journal entry compatible với FE hiện tại.

    FE gửi:
      - text_content: string (bắt buộc)
      - tags: JSON string của array [{tag_id, tag_name}]
      - audio: file .m4a hoặc .mp3 (tuỳ chọn)
      - (emotion_label hiện chưa gửi) => default 'Neutral' nếu thiếu / invalid
    """
    form_data = await request.form()

    # Parse tags: FE gửi JSON string của list object => map sang list tên
    raw_tags = form_data.get("tags")
    parsed_tags: Optional[List[str]] = None
    if raw_tags:
        try:
            import json
            tags_obj = json.loads(raw_tags)
            if isinstance(tags_obj, list):
                parsed_tags = []
                for t in tags_obj:
                    if isinstance(t, dict):
                        name = t.get("tag_name") or t.get("name")
                        if name:
                            parsed_tags.append(str(name))
            # Deduplicate & clean
            if parsed_tags:
                cleaned = []
                for tag in parsed_tags:
                    tag = tag.strip()
                    if tag and tag not in cleaned:
                        cleaned.append(tag)
                parsed_tags = cleaned or None
        except Exception:
            # Nếu parse lỗi => bỏ qua tags
            parsed_tags = None

    emotion_label = form_data.get("emotion_label")
    # FE không gửi => đặt mặc định Neutral
    if not emotion_label or emotion_label not in ICON_SENTIMENT_MAP:
        emotion_label = "Neutral"

    data = JournalCreate(
        emotion_label=emotion_label,
        text_content=form_data.get("text_content"),
        voice_note_path=None if not audio else "temp_path",
        tags=parsed_tags
    )

    file_path: Optional[str] = None
    try:
        # Validate text_content
        if not data.text_content or not data.text_content.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text content is required")

        # Validate tags length
        if data.tags and any(len(tag) > 50 for tag in data.tags):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Each tag must be <= 50 characters")

        # Handle audio file (.mp3 / .m4a)
        if audio:
            file_extension = os.path.splitext(audio.filename)[1].lower()
            if file_extension not in (".mp3", ".m4a"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only MP3 or M4A files are supported")
            file_name = f"{uuid.uuid4()}{file_extension}"
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(await audio.read())
            data.voice_note_path = file_path

        # Create journal
        service = JournalService(JournalRepository(db))
        journal = await service.create_journal(str(current_user["_id"]), data)
        return serialize_journal(journal)
    except HTTPException:
        # Re-raise có kiểm soát
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create journal: {str(e)}")
    finally:
        if audio and file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

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