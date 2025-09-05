from transformers import pipeline
from bson import ObjectId
from app.repositories.journal_repository import JournalRepository
from app.schemas.journal_schema import JournalCreate
from app.models.journal_model import Journal
from app.core.constants import ICON_SENTIMENT_MAP
from app.core.config import settings

# Chọn model dựa trên .env
if settings.SENTIMENT_MODEL.lower() == "roberta":
    MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"
else:
    MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

print(f"Loading sentiment model: {MODEL_NAME}")

sentiment_pipeline = pipeline("sentiment-analysis", model=MODEL_NAME)

def analyze_sentiment(text: str):
    if not text:
        return "Neutral", 0.0

    result = sentiment_pipeline(text)[0]  # {'label': 'LABEL_2', 'score': 0.98}
    raw_label = result["label"]

    # Mapping HuggingFace output → human-readable
    label_map = {
        "LABEL_0": "Negative",
        "LABEL_1": "Neutral",
        "LABEL_2": "Positive",
    }
    label = label_map.get(raw_label, "Neutral")

    score = (
        result["score"] if label == "Positive"
        else -result["score"] if label == "Negative"
        else 0.0
    )
    return label, score

class JournalService:
    def __init__(self, journal_repo: JournalRepository):
        self.journal_repo = journal_repo

    async def create_journal(self, user_id: str, data: JournalCreate) -> Journal:
        journal_dict = data.dict()
        journal_dict["user_id"] = ObjectId(user_id)

        if data.text_content:
            ai_label, ai_score = analyze_sentiment(data.text_content)
            icon_label, icon_score = ICON_SENTIMENT_MAP.get(data.emotion_label, ("Neutral", 0.0))

            # Nếu icon và AI cùng nhãn -> lấy trung bình score
            if ai_label == icon_label:
                label, score = ai_label, (ai_score + icon_score) / 2
            else:
                # Ưu tiên AI nhưng vẫn giữ icon làm reference
                label, score = ai_label, ai_score
        else:
            label, score = ICON_SENTIMENT_MAP.get(data.emotion_label, ("Neutral", 0.0))

        journal_dict["sentiment_label"] = label
        journal_dict["sentiment_score"] = score

        return await self.journal_repo.create(journal_dict)

    async def get_user_journals(self, user_id: str) -> list[Journal]:
        return await self.journal_repo.get_by_user(user_id)