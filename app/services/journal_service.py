import asyncio
from bson import ObjectId
from app.repositories.journal_repository import JournalRepository
from app.schemas.journal_schema import JournalCreate
from app.models.journal_model import Journal
from app.core.constants import ICON_SENTIMENT_MAP
from app.core.config import settings
import assemblyai as aai
from transformers import pipeline

# Set AssemblyAI API key
aai.settings.api_key = settings.ASSEMBLYAI_API_KEY

# Initialize sentiment analysis pipeline
if settings.SENTIMENT_MODEL.lower() == "roberta":
    SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
else:
    SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
sentiment_pipeline = pipeline("sentiment-analysis", model=SENTIMENT_MODEL)

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

    async def create_journal(self, user_id: str, data: JournalCreate) -> Journal:
        """Create a new journal entry with STT and sentiment analysis."""
        journal_dict = data.dict(exclude_unset=True)
        journal_dict["user_id"] = ObjectId(user_id)

        # Collect all text sources for comprehensive sentiment analysis
        text_sources = []
        
        # Process voice note if provided
        if data.voice_note_path:
            with open(data.voice_note_path, "rb") as f:
                voice_text = await self.transcribe_audio(f.read())
            journal_dict["voice_text"] = voice_text
            if voice_text and not voice_text.startswith("Transcription error"):
                text_sources.append(voice_text)
        
        # Add text content if provided
        if data.text_content:
            text_sources.append(data.text_content)
        
        # Combine all text for sentiment analysis
        combined_text = " ".join(text_sources).strip()

        if combined_text:
            # AI sentiment analysis on combined text
            ai_label, ai_score = analyze_sentiment(combined_text)
            
            # User emotion from icon selection
            icon_label, icon_score = ICON_SENTIMENT_MAP.get(data.emotion_label, ("Neutral", 0.0))
            
            # Weighted combination: 70% AI + 30% user emotion
            # Use AI label but blend scores for nuanced result
            if ai_label == icon_label:
                # Agreement: average both scores
                score = (ai_score * 0.7) + (icon_score * 0.3)
                label = ai_label
            else:
                # Disagreement: trust AI more but consider user input
                score = (ai_score * 0.7) + (icon_score * 0.3)
                # Use AI label unless user picked strong emotion (|icon_score| > 0.7)
                label = icon_label if abs(icon_score) > 0.7 else ai_label
        else:
            # No text: use only user emotion
            label, score = ICON_SENTIMENT_MAP.get(data.emotion_label, ("Neutral", 0.0))

        journal_dict["sentiment_label"] = label
        journal_dict["sentiment_score"] = round(score, 2)
        journal_dict["tags"] = data.tags or []  # Ensure tags is List[str]
        return await self.journal_repo.create(journal_dict)

    async def get_user_journals(self, user_id: str) -> list[Journal]:
        """Retrieve all journals for a user."""
        return await self.journal_repo.get_by_user(user_id)