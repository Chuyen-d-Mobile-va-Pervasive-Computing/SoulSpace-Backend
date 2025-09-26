from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from bson import ObjectId
from app.repositories.journal_repository import JournalRepository
from app.schemas.journal_schema import JournalCreate
from app.models.journal_model import Journal
from app.core.constants import ICON_SENTIMENT_MAP
from app.core.config import settings
import logging
import os
import torch
import soundfile as sf
import librosa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize sentiment analysis pipeline
if settings.SENTIMENT_MODEL.lower() == "roberta":
    SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
else:
    SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
logger.info(f"Loading sentiment model: {SENTIMENT_MODEL}")
sentiment_pipeline = pipeline("sentiment-analysis", model=SENTIMENT_MODEL)

# Initialize Whisper Medium for English speech-to-text
WHISPER_MODEL = "openai/whisper-medium"
logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
processor = AutoProcessor.from_pretrained(WHISPER_MODEL)
model = AutoModelForSpeechSeq2Seq.from_pretrained(WHISPER_MODEL)
model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(language="en", task="transcribe")

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
        self.processor = processor
        self.model = model

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe an English MP3 audio file to text using Whisper Medium."""
        try:
            if not audio_path or not os.path.exists(audio_path):
                raise ValueError("Audio file path is invalid or does not exist")

            # Load and decode MP3 file to raw audio
            audio_data, samplerate = sf.read(audio_path, dtype="float32")
            if samplerate != 16000:
                logger.warning(f"Resampling audio from {samplerate}Hz to 16000Hz")
                audio_data = librosa.resample(audio_data, orig_sr=samplerate, target_sr=16000)

            # Process audio for Whisper
            input_features = self.processor(audio_data, sampling_rate=16000, return_tensors="pt").input_features

            # Perform transcription
            with torch.no_grad():
                predicted_ids = self.model.generate(input_features)
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            logger.info(f"Transcribed audio to text: {transcription}")
            return transcription
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return f"Transcription error: {str(e)}"

    async def create_journal(self, user_id: str, data: JournalCreate) -> Journal:
        """Create a new journal entry with STT and sentiment analysis."""
        journal_dict = data.dict(exclude_unset=True)
        journal_dict["user_id"] = ObjectId(user_id)

        if data.voice_note_path:
            voice_text = self.transcribe_audio(data.voice_note_path)
            journal_dict["voice_text"] = voice_text
            text = voice_text
        elif data.text_content:
            text = data.text_content
        else:
            text = ""

        if text:
            ai_label, ai_score = analyze_sentiment(text)
            icon_label, icon_score = ICON_SENTIMENT_MAP.get(data.emotion_label, ("Neutral", 0.0))
            label, score = ai_label, (ai_score + icon_score) / 2 if ai_label == icon_label else ai_score
        else:
            label, score = ICON_SENTIMENT_MAP.get(data.emotion_label, ("Neutral", 0.0))

        journal_dict["sentiment_label"] = label
        journal_dict["sentiment_score"] = score
        return await self.journal_repo.create(journal_dict)

    async def get_user_journals(self, user_id: str) -> list[Journal]:
        """Retrieve all journals for a user."""
        return await self.journal_repo.get_by_user(user_id)