from fastapi import APIRouter, Depends, HTTPException
from app.schemas.journal_schema import JournalCreate, JournalResponse
from app.repositories.journal_repository import JournalRepository
from app.services.journal_service import JournalService
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/journal", tags=["journal"])

# Helper để serialize Journal → JournalResponse
def serialize_journal(journal) -> JournalResponse:
    return JournalResponse(
        id=str(journal.id),
        user_id=str(journal.user_id),
        created_at=journal.created_at,
        emotion_label=journal.emotion_label,
        emotion_emoji=journal.emotion_emoji,
        text_content=journal.text_content,
        sentiment_label=journal.sentiment_label,
        sentiment_score=journal.sentiment_score,
        tags=journal.tags,
    )

@router.post("/", response_model=JournalResponse)
async def create_journal(
    data: JournalCreate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = JournalService(JournalRepository(db))
    journal = await service.create_journal(current_user["_id"], data)
    return serialize_journal(journal)

@router.get("/", response_model=list[JournalResponse])
async def get_journals(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = JournalService(JournalRepository(db))
    journals = await service.get_user_journals(current_user["_id"])
    return [serialize_journal(j) for j in journals]