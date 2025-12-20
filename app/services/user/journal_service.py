# app/services/user/journal_service.py
import asyncio
from bson import ObjectId
from typing import Optional, List
from app.repositories.journal_repository import JournalRepository
from app.schemas.user.journal_schema import JournalCreate
from app.models.journal_model import Journal
from app.core.constants import ICON_SENTIMENT_MAP
from app.core.config import settings
from app.services.common.toxic_detection_service import get_toxic_detection_service
import assemblyai as aai
from transformers import pipeline
from datetime import datetime, date, time

# Set AssemblyAI API key
aai.settings.api_key = settings.ASSEMBLYAI_API_KEY

# Initialize sentiment analysis pipeline
if settings.SENTIMENT_MODEL.lower() == "roberta":
    SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
else:
    SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=SENTIMENT_MODEL,
    framework="pt"
)

def analyze_sentiment(text: str):
    """Analyze sentiment of the given text."""
    if not text:
        return "Neutral", 0.0
    result = sentiment_pipeline(text)[0]
    raw_label = result["label"]
    label_map = {"LABEL_0": "Negative", "LABEL_1": "Neutral", "LABEL_2": "Positive"}
    label = label_map.get(raw_label, "Neutral")
    score = result["score"] if label == "Positive" else -result["score"] if label == "Negative" else 0.0
    return label, score

class JournalService:
    def __init__(self, journal_repo: JournalRepository):
        self.journal_repo = journal_repo
        self.toxic_service = get_toxic_detection_service()

    async def transcribe_audio(self, audio_content: bytes) -> str:
        """Transcribe an English MP3 audio from bytes using AssemblyAI (async wrapper)."""
        try:
            if not audio_content:
                raise ValueError("Audio content is empty")
            def _transcribe():
                transcriber = aai.Transcriber()
                transcript = transcriber.transcribe(audio_content)
                if transcript.status == aai.TranscriptStatus.error:
                    raise Exception(f"Transcription error: {transcript.error}")
                return transcript.text
            transcription = await asyncio.to_thread(_transcribe)
            return transcription
        except Exception as e:
            return f"Transcription error: {str(e)}"

    async def create_journal(
        self,
        user_id: str,
        emotion_label: Optional[str] = None,
        text_content: Optional[str] = None,
        voice_note_path: Optional[str] = None,
        voice_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        journal_date: Optional[date] = None
    ) -> Journal:
        # 1. AI TOXIC DETECTION
        toxic_labels = []
        toxic_confidence = 0.0
        is_toxic = False
        toxic_predictions = {}

        texts_to_check = []
        if text_content:
            texts_to_check.append(text_content)
        if voice_text:
            texts_to_check.append(voice_text)

        if texts_to_check and await self.toxic_service.check_health():
            try:
                result = await self.toxic_service.analyze_text(texts_to_check[0], threshold=0.5)
                toxic_predictions = result.predictions
                if result.is_violation:
                    is_toxic = True
                    toxic_labels.extend(result.toxic_labels)
                    toxic_confidence = result.confidence
                for text in texts_to_check[1:]:
                    res = await self.toxic_service.analyze_text(text, threshold=0.5)
                    for label, prob in res.predictions.items():
                        toxic_predictions[label] = max(toxic_predictions.get(label, 0), prob)
                    if res.is_violation:
                        is_toxic = True
                        toxic_labels.extend(res.toxic_labels)
                        toxic_confidence = max(toxic_confidence, res.confidence)
                toxic_labels = list(set(toxic_labels))
            except Exception as e:
                print(f"[TOXIC DETECTION ERROR] Journal: {e}")

        # 2. Sentiment
        sentiment_label = "Neutral"
        sentiment_score = 0.0
        if emotion_label and emotion_label in ICON_SENTIMENT_MAP:
            sentiment_label, sentiment_score = ICON_SENTIMENT_MAP[emotion_label]

        # 3. Xử lý created_at
        if journal_date:
            if journal_date > datetime.utcnow().date():
                raise ValueError("Journal date cannot be in the future")
            created_at = datetime.combine(journal_date, time.min)
        else:
            created_at = datetime.utcnow()

        # 4. Tạo dict dữ liệu thuần (KHÔNG tạo Journal model ở đây)
        journal_data = {
            "user_id": ObjectId(user_id),
            "created_at": created_at,
            "emotion_label": emotion_label,
            "text_content": text_content,
            "voice_note_path": voice_note_path,
            "voice_text": voice_text,
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "tags": tags or [],
            "is_toxic": is_toxic,
            "toxic_labels": toxic_labels,
            "toxic_confidence": toxic_confidence,
            "toxic_predictions": toxic_predictions
        }

        # 5. Insert - MongoDB tự generate _id kiểu ObjectId
        result = await self.journal_repo.collection.insert_one(journal_data)

        # 6. Lấy lại document đầy đủ (có _id thật từ MongoDB)
        created_doc = await self.journal_repo.collection.find_one({"_id": result.inserted_id})

        if not created_doc:
            raise ValueError("Failed to create journal")

        # 7. Tạo Journal model từ document đã có _id ObjectId
        created_journal = Journal(**created_doc)

        return created_journal

    async def get_user_journals(self, user_id: str) -> list[Journal]:
        """Retrieve all journals for a user."""
        return await self.journal_repo.get_by_user(user_id)
    
    async def get_journal_detail(self, journal_id: str, user_id: str) -> Journal:
        """
        Lấy chi tiết journal và kiểm tra quyền sở hữu.
        Raises ValueError nếu không tìm thấy, PermissionError nếu không phải chủ.
        """
        journal = await self.journal_repo.get_by_id(journal_id)

        if not journal:
            raise ValueError("NOT_FOUND")

        if str(journal.user_id) != user_id:
            raise PermissionError("FORBIDDEN")

        return journal