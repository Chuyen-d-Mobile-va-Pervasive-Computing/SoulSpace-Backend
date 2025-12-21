from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Query
from app.schemas.user.journal_schema import JournalCreate, JournalResponse
from app.repositories.journal_repository import JournalRepository
from app.services.user.journal_service import JournalService
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.constants import ICON_SENTIMENT_MAP
from typing import List, Optional
import uuid
import os
from time import time
from datetime import datetime, date
from bson import ObjectId
import traceback

router = APIRouter(prefix="/journal", tags=["User - Journal (Nhật ký)"])

def serialize_journal(journal) -> JournalResponse:
    """Serialize Journal model to JournalResponse schema."""
    return JournalResponse(
        id=str(journal.id),
        user_id=str(journal.user_id),
        created_at=journal.created_at,
        emotion_label=journal.emotion_label or "Neutral",
        text_content=journal.text_content or "",
        voice_note_path=journal.voice_note_path,
        voice_text=journal.voice_text,
        sentiment_label=journal.sentiment_label or "Neutral",
        sentiment_score=journal.sentiment_score or 0.0,
        tags=journal.tags or [],
        is_toxic=journal.is_toxic,
        toxic_labels=journal.toxic_labels,
        toxic_confidence=journal.toxic_confidence,
        toxic_predictions=journal.toxic_predictions
    )

@router.get("/analytics")
async def get_emotion_analytics(
    period: str = Query(..., regex="^(week|month|year)$", description="Loại kỳ: week, month, year"),
    start_date: date = Query(..., description="Ngày bắt đầu (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Ngày kết thúc (YYYY-MM-DD)"),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Lấy thống kê cảm xúc (chart + stats) theo tuần/tháng/năm.
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date"
        )

    today = datetime.utcnow().date()
    if end_date > today:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be in the future"
        )

    service = JournalService(JournalRepository(db))
    try:
        data = await service.get_emotion_analytics(
            user_id=str(current_user["_id"]),
            period=period,
            start=start_date,  
            end=end_date      
        )
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in get_emotion_analytics: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing analytics"
        )

@router.post("/", response_model=JournalResponse)
async def create_journal(
    request: Request,
    audio: UploadFile = File(None, description="Optional audio recording (.mp3 or .m4a)"),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    form_data = await request.form()

    # Parse tags từ JSON string (FE gửi tags dưới dạng JSON)
    raw_tags = form_data.get("tags")
    parsed_tags: List[str] = []
    if raw_tags:
        try:
            import json
            tags_obj = json.loads(raw_tags)
            if isinstance(tags_obj, list):
                parsed_tags = [t.get("tag_name") or t.get("name") for t in tags_obj if isinstance(t, dict)]
                parsed_tags = [tag.strip() for tag in parsed_tags if tag.strip()]
        except Exception:
            pass

    emotion_label = form_data.get("emotion_label")
    if not emotion_label or emotion_label not in ICON_SENTIMENT_MAP:
        emotion_label = "Neutral"

    # Tạo JournalCreate để validate (không cần journal_date ở đây vì date không validate bằng Pydantic ở form)
    data = JournalCreate(
        emotion_label=emotion_label,
        text_content=form_data.get("text_content"),
        voice_note_path=None,
        tags=parsed_tags
    )

    # Parse journal_date từ form (NEW)
    raw_journal_date = form_data.get("journal_date")
    journal_date: Optional[date] = None
    if raw_journal_date:
        try:
            journal_date = date.fromisoformat(raw_journal_date)
            if journal_date > datetime.utcnow().date():
                raise HTTPException(status_code=400, detail="Journal date cannot be in the future")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid journal_date format. Use YYYY-MM-DD")

    file_path = None
    voice_text = None  # Sẽ set nếu có audio
    try:
        if not data.text_content or not data.text_content.strip():
            raise HTTPException(status_code=400, detail="Text content is required")

        # Xử lý audio + STT
        if audio:
            file_extension = os.path.splitext(audio.filename)[1].lower()
            if file_extension not in (".mp3", ".m4a"):
                raise HTTPException(status_code=400, detail="Only MP3 or M4A files are supported")
           
            file_name = f"{uuid.uuid4()}{file_extension}"
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, file_name)
           
            with open(file_path, "wb") as f:
                f.write(await audio.read())
           
            # Transcribe audio
            service = JournalService(JournalRepository(db))
            voice_text = await service.transcribe_audio(open(file_path, "rb").read())
           
            # Update voice_note_path (giữ tạm để pass xuống service)
            data.voice_note_path = file_path  # xóa ở finally

        # Gọi service với primitive values + journal_date (NEW)
        service = JournalService(JournalRepository(db))
        journal = await service.create_journal(
            user_id=str(current_user["_id"]),
            emotion_label=data.emotion_label,
            text_content=data.text_content,
            voice_note_path=data.voice_note_path,
            voice_text=voice_text,
            tags=data.tags,
            journal_date=journal_date
        )

        return serialize_journal(journal)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create journal: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
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
   
@router.get("/{journal_id}", response_model=JournalResponse)
async def get_journal_detail(
    journal_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Lấy chi tiết một journal cụ thể.
    Chỉ chủ sở hữu mới được xem.
    """
    # Validate ObjectId format sớm
    if not ObjectId.is_valid(journal_id):
        raise HTTPException(status_code=400, detail="Invalid journal id")

    service = JournalService(JournalRepository(db))

    try:
        journal = await service.get_journal_detail(
            journal_id=journal_id,
            user_id=str(current_user["_id"])
        )
        return serialize_journal(journal)

    except ValueError:
        raise HTTPException(status_code=404, detail="Journal not found")
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view this journal"
        )