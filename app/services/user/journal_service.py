import asyncio
from bson import ObjectId
from typing import Optional, List, Tuple
from app.repositories.journal_repository import JournalRepository
from app.schemas.user.journal_schema import JournalCreate
from app.models.journal_model import Journal
from app.core.constants import ICON_SENTIMENT_MAP
from app.core.config import settings
from app.services.common.toxic_detection_service import get_toxic_detection_service
import assemblyai as aai
from transformers import pipeline
from datetime import datetime, date, time, timedelta
from typing import Dict, List
import calendar

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
    
    def _get_group_key(self, period: str):
        return (
            {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}}
            if period == "year"
            else {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}
        )

    def _validate_period_range(self, period: str, start: date, end: date):
        if period == "week":
            if (end - start).days != 6:
                raise ValueError("Week period must be exactly 7 days")

        elif period == "month":
            if start.year != end.year or start.month != end.month:
                raise ValueError("Month period must be within the same month")

        elif period == "year":
            if start.year != end.year:
                raise ValueError("Year period must be within the same year")

    def _normalize_year_range(self, period: str, start: date, end: date) -> Tuple[date, date]:
        if period == "year":
            return date(start.year, 1, 1), date(start.year, 12, 31)
        return start, end

    def _format_chart_data(self, results, period, start, end):
        data_map = {r["_id"]: r for r in results}
        chart = []

        if period == "year":
            for m in range(1, 13):
                key = f"{start.year}-{m:02d}"
                r = data_map.get(key, {})
                chart.append({
                    "date": key,
                    "positive_count": r.get("positive_count", 0),
                    "negative_count": r.get("negative_count", 0),
                    "neutral_count": r.get("neutral_count", 0),
                    "total_entries": r.get("total_entries", 0),
                })
        else:
            cur = start
            while cur <= end:
                key = cur.strftime("%Y-%m-%d")
                r = data_map.get(key, {})
                chart.append({
                    "date": key,
                    "positive_count": r.get("positive_count", 0),
                    "negative_count": r.get("negative_count", 0),
                    "neutral_count": r.get("neutral_count", 0),
                    "total_entries": r.get("total_entries", 0),
                })
                cur += timedelta(days=1)
        return chart

    def _calculate_current_stats(self, chart):
        total = sum(i["total_entries"] for i in chart)
        pos = sum(i["positive_count"] for i in chart)
        neg = sum(i["negative_count"] for i in chart)

        return {
            "total_entries": total,
            "positive_percentage": round(pos / total * 100, 1) if total else 0.0,
            "negative_percentage": round(neg / total * 100, 1) if total else 0.0,
        }

    async def _calculate_trends(self, user_id, period, start, end, curr_stats):
        prev_start, prev_end = self._previous_period(period, start)

        pipeline = [
            {"$match": {
                "user_id": ObjectId(user_id),
                "created_at": {"$gte": datetime.combine(prev_start, time.min),
                               "$lte": datetime.combine(prev_end, time.max)}
            }},
            {"$group": {
                "_id": self._get_group_key(period),
                "positive_count": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "Positive"]}, 1, 0]}},
                "negative_count": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "Negative"]}, 1, 0]}},
                "neutral_count": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "Neutral"]}, 1, 0]}},
                "total_entries": {"$sum": 1}
            }}
        ]

        prev = await self.journal_repo.collection.aggregate(pipeline).to_list(None)

        if not prev and curr_stats["total_entries"] > 0:
            return {
                "trend_positive": "up",
                "trend_negative": "equal",
                "trend_entries": "up"
            }

        if not prev:
            return {"trend_positive": "equal", "trend_negative": "equal", "trend_entries": "equal"}

        prev_chart = self._format_chart_data(prev, period, prev_start, prev_end)
        prev_stats = self._calculate_current_stats(prev_chart)

        def trend(curr, prev):
            if prev == 0:
                return "up" if curr > 0 else "equal"
            diff = (curr - prev) / prev * 100
            if abs(diff) < 5:
                return "equal"
            return "up" if diff > 0 else "down"

        return {
            "trend_positive": trend(curr_stats["positive_percentage"], prev_stats["positive_percentage"]),
            "trend_negative": trend(curr_stats["negative_percentage"], prev_stats["negative_percentage"]),
            "trend_entries": trend(curr_stats["total_entries"], prev_stats["total_entries"]),
        }

    def _previous_period(self, period, start):
        if period == "week":
            return start - timedelta(days=7), start - timedelta(days=1)
        if period == "month":
            prev_month = start.month - 1 or 12
            prev_year = start.year - 1 if start.month == 1 else start.year
            last = calendar.monthrange(prev_year, prev_month)[1]
            return date(prev_year, prev_month, 1), date(prev_year, prev_month, last)
        return date(start.year - 1, 1, 1), date(start.year - 1, 12, 31)

    async def get_emotion_analytics(self, user_id, period, start, end):
        self._validate_period_range(period, start, end)
        start, end = self._normalize_year_range(period, start, end)

        pipeline = [
            {"$match": {
                "user_id": ObjectId(user_id),
                "created_at": {"$gte": datetime.combine(start, time.min),
                               "$lte": datetime.combine(end, time.max)}
            }},
            {"$group": {
                "_id": self._get_group_key(period),
                "positive_count": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "Positive"]}, 1, 0]}},
                "negative_count": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "Negative"]}, 1, 0]}},
                "neutral_count": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "Neutral"]}, 1, 0]}},
                "total_entries": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]

        results = await self.journal_repo.collection.aggregate(pipeline).to_list(None)
        chart = self._format_chart_data(results, period, start, end)
        stats = self._calculate_current_stats(chart)

        trends = await self._calculate_trends(user_id, period, start, end, stats)
        stats.update(trends)

        if period == "year":
            total_pos = sum(i["positive_count"] for i in chart)
            total = sum(i["total_entries"] for i in chart)
            stats["average_positive"] = round(total_pos / total * 100, 1) if total else 0.0

        return {
            "period": period,
            "range": {"start": start.isoformat(), "end": end.isoformat()},
            "chart_data": chart,
            "stats": stats
        }
        
    async def get_daily_sentiment_for_date(
        self,
        user_id: str,
        target_date: date
    ) -> Dict:
        """
        Lấy điểm trung bình sentiment_score cho một ngày cụ thể.
        Nếu không có nhật ký → average_score = None, entry_count = 0
        """
        start_of_day = datetime.combine(target_date, time.min)
        end_of_day = datetime.combine(target_date, time.max)

        pipeline = [
            {
                "$match": {
                    "user_id": ObjectId(user_id),
                    "created_at": {
                        "$gte": start_of_day,
                        "$lte": end_of_day
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "average_score": {"$avg": "$sentiment_score"},
                    "entry_count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "average_score": {"$round": [{"$ifNull": ["$average_score", None]}, 2]},
                    "entry_count": 1
                }
            }
        ]

        results = await self.journal_repo.collection.aggregate(pipeline).to_list(1)

        if not results:
            # Không có nhật ký nào trong ngày
            return {
                "date": target_date.isoformat(),
                "average_score": None,
                "entry_count": 0
            }

        result = results[0]
        result["date"] = target_date.isoformat()
        return result   
        
    async def delete_journal(self, journal_id: str, user_id: str) -> bool:
        """
        Xóa journal - chỉ chủ sở hữu mới được xóa.
        Returns True nếu xóa thành công, False nếu không tìm thấy.
        Raises PermissionError nếu không phải chủ sở hữu.
        """
        journal = await self.journal_repo.get_by_id(journal_id)

        if not journal:
            return False 

        if str(journal.user_id) != user_id:
            raise PermissionError("You do not have permission to delete this journal")

        result = await self.journal_repo.collection.delete_one({"_id": ObjectId(journal_id)})
        
        return result.deleted_count > 0