from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Query
from app.schemas.user.journal_schema import JournalCreate, JournalResponse, DailySentimentResponse
from app.repositories.journal_repository import JournalRepository
from app.services.user.journal_service import JournalService
from app.services.user.user_tree_service import PositiveActionNotFoundError, get_user_tree_service
from app.services.user.journal_tree_orchestrator import JournalTreeOrchestrator
from app.core.constants import ICON_SENTIMENT_MAP
from app.core.database import get_db
from app.core.dependencies import get_current_user
from typing import List, Optional
import uuid
import os
from time import time
from datetime import datetime, date, timezone
from bson import ObjectId
import traceback
import json
import logging
 
router = APIRouter(prefix="/journal", tags=["User - Journal (Nhật ký)"])
 
def serialize_journal(journal) -> JournalResponse:
    """
    Serialize Journal model to JournalResponse schema.
    Trả về UTC datetime - FE sẽ convert sang giờ VN khi hiển thị.
    """
    # Đảm bảo created_at là UTC aware
    if journal.created_at.tzinfo is None:
        utc_created = journal.created_at.replace(tzinfo=timezone.utc)
    else:
        utc_created = journal.created_at.astimezone(timezone.utc)
   
    return JournalResponse(
        id=str(journal.id),
        user_id=str(journal.user_id),
        created_at=utc_created,  # Trả về UTC datetime
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
   
@router.get("/daily-sentiment", response_model=DailySentimentResponse)
async def get_daily_sentiment(
    date: date = Query(..., description="Ngày cần lấy thống kê (YYYY-MM-DD) - theo giờ VN"),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Lấy điểm trung bình sentiment_score cho một ngày cụ thể.
    FE truyền date theo giờ VN, BE convert sang UTC range để query.
    """
    service = JournalService(JournalRepository(db))
    try:
        result = await service.get_daily_sentiment_for_date(
            user_id=str(current_user["_id"]),
            target_date=date
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.exception("Error in get_daily_sentiment: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching daily sentiment"
        )
       
@router.get("/analytics")
async def get_emotion_analytics(
    period: str = Query(..., regex="^(week|month|year)$", description="Loại kỳ: week, month, year"),
    start_date: date = Query(..., description="Ngày bắt đầu (YYYY-MM-DD) - theo giờ VN"),
    end_date: date = Query(..., description="Ngày kết thúc (YYYY-MM-DD) - theo giờ VN"),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Lấy thống kê cảm xúc theo tuần/tháng/năm.
    FE truyền dates theo giờ VN, BE convert sang UTC để query.
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date"
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
 
@router.post("/", status_code=201)
async def create_journal_enhanced(
    request: Request,
    audio: Optional[UploadFile] = File(None, description="Optional audio (.mp3 or .m4a)"),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tree_service=Depends(get_user_tree_service),
):
    """
    Tạo journal mới + tự động tưới cây.
    
    Response trả về created_at ở UTC - FE sẽ convert sang giờ VN để hiển thị.
    """
    form_data = await request.form()
 
    # 1. Parse tags
    raw_tags = form_data.get("tags")
    parsed_tags: List[str] = []
    if raw_tags:
        try:
            tags_obj = json.loads(raw_tags)
            if isinstance(tags_obj, list):
                parsed_tags = [
                    (t.get("tag_name") or t.get("name") or "").strip()
                    for t in tags_obj if isinstance(t, dict)
                ]
                parsed_tags = [tag for tag in parsed_tags if tag]
        except json.JSONDecodeError:
            pass
 
    # 2. Parse emotion_label
    emotion_label = form_data.get("emotion_label")
    if not emotion_label or emotion_label not in ICON_SENTIMENT_MAP:
        emotion_label = "Neutral"
 
    # 3. Parse journal_date (FE gửi theo giờ VN)
    raw_journal_date = form_data.get("journal_date")
    journal_date: Optional[date] = None
    if raw_journal_date:
        try:
            journal_date = date.fromisoformat(raw_journal_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid journal_date format. Use YYYY-MM-DD")
 
    # 4. Validate text_content
    text_content = form_data.get("text_content")
    if not text_content or not str(text_content).strip():
        raise HTTPException(status_code=400, detail="Text content is required")
 
    # 5. Xử lý audio
    file_path = None
    voice_text = None
    voice_note_path = None
 
    try:
        if audio and audio.filename:
            file_extension = os.path.splitext(audio.filename)[1].lower()
            if file_extension not in {".mp3", ".m4a"}:
                raise HTTPException(status_code=400, detail="Only MP3 or M4A files are supported")
 
            file_name = f"{uuid.uuid4()}{file_extension}"
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, file_name)
 
            with open(file_path, "wb") as f:
                f.write(await audio.read())
 
            transcribe_service = JournalService(JournalRepository(db))
            voice_text = await transcribe_service.transcribe_audio(open(file_path, "rb").read())
            voice_note_path = file_path
 
        # 6. Khởi tạo orchestrator
        journal_service = JournalService(JournalRepository(db))
        orchestrator = JournalTreeOrchestrator(
            journal_service=journal_service,
            tree_service=tree_service
        )
 
        # 7. Tạo journal + tưới cây
        result = await orchestrator.create_journal_with_enhancements(
            user_id=str(current_user["_id"]),
            emotion_label=emotion_label,
            text_content=text_content,
            voice_note_path=voice_note_path,
            voice_text=voice_text,
            tags=parsed_tags,
            journal_date=journal_date
        )
 
        return result
 
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Unexpected error in create_journal_enhanced: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create journal due to internal error")
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
    """
    Lấy tất cả journals của user.
    Trả về UTC timestamps - FE convert sang giờ VN khi hiển thị.
    """
    try:
        service = JournalService(JournalRepository(db))
        journals = await service.get_user_journals(str(current_user["_id"]))
        return [serialize_journal(j) for j in journals]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to fetch journals: {str(e)}"
        )

@router.post("/test-stt", response_model=dict)
async def test_stt(
    voice_note: UploadFile = File(..., description="Upload MP3 for transcription"),
):
    """Test Speech-to-Text với file MP3."""
    file_path = None
    try:
        file_extension = os.path.splitext(voice_note.filename)[1].lower()
        if file_extension != ".mp3":
            raise HTTPException(status_code=400, detail="Only MP3 files are supported")
 
        file_name = f"{uuid.uuid4()}{file_extension}"
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file_name)
        start_time = time()
        
        with open(file_path, "wb") as f:
            f.write(await voice_note.read())
 
        service = JournalService(None)
        voice_text = await service.transcribe_audio(open(file_path, "rb").read())
        processing_time = time() - start_time
 
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
    Lấy chi tiết journal.
    Trả về UTC timestamp - FE convert sang giờ VN.
    """
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
        
@router.delete("/{journal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal(
    journal_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Xóa journal - chỉ chủ sở hữu được phép."""
    if not ObjectId.is_valid(journal_id):
        raise HTTPException(status_code=400, detail="Invalid journal id")
 
    service = JournalService(JournalRepository(db))
 
    try:
        deleted = await service.delete_journal(
            journal_id=journal_id,
            user_id=str(current_user["_id"])
        )
 
        if not deleted:
            raise HTTPException(status_code=404, detail="Journal not found")
 
        return None
 
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this journal"
        )
    except Exception as e:
        print(f"Error deleting journal: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete journal")