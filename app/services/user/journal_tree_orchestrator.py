# app/services/user/journal_tree_orchestrator.py
from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId

from app.models.journal_model import Journal
from app.services.user.journal_service import JournalService
from app.services.user.user_tree_service import UserTreeService

POSITIVE_EMOTIONS = {"Happy", "Excited"}

class JournalTreeOrchestrator:
    def __init__(
        self,
        journal_service: JournalService,
        tree_service: UserTreeService
    ):
        self.journal_service = journal_service
        self.tree_service = tree_service

    async def create_journal_with_enhancements(
        self,
        user_id: str,
        emotion_label: Optional[str],
        text_content: Optional[str],
        voice_note_path: Optional[str],
        voice_text: Optional[str],
        tags: Optional[List[str]],
        journal_date: Optional[datetime.date]
    ) -> Dict:
        journal = await self.journal_service.create_journal(
            user_id=user_id,
            emotion_label=emotion_label,
            text_content=text_content,
            voice_note_path=voice_note_path,
            voice_text=voice_text,
            tags=tags,
            journal_date=journal_date
        )

        watered = False
        tree_result = None
        share_suggestion = False

        is_positive = (
            journal.sentiment_label == "Positive" or
            (emotion_label and emotion_label in POSITIVE_EMOTIONS)
        )

        if (
            not journal.is_toxic
            and text_content
            and text_content.strip()
            and is_positive
        ):
            tree_status = await self.tree_service.get_user_tree_status(ObjectId(user_id))

            if tree_status.get("can_water_today", False):
                action_doc = await self.tree_service.action_repo.collection.find_one({
                    "action_name": "Write Journal"
                })

                if not action_doc:
                    raise ValueError("Default action 'Write Journal' not found in database")

                action_id = action_doc["_id"]
                positive_thoughts = self._generate_positive_thoughts(emotion_label or "Neutral")

                updated_tree = await self.tree_service.nourish_tree(
                    user_id=ObjectId(user_id),
                    action_id=action_id,
                    positive_thoughts=positive_thoughts
                )

                watered = True
                tree_result = {
                    "watered": True,
                    "xp_gained": 10,
                    "current_level": updated_tree["current_level_calculated"],
                    "current_xp": updated_tree["current_xp_in_level"],
                    "xp_for_next_level": updated_tree["xp_for_next_level"],
                    "streak_days": updated_tree["streak_days"],
                    "message": "Tree watered successfully! +10 XP"
                }
                share_suggestion = True

        if not watered:
            tree_status = await self.tree_service.get_user_tree_status(ObjectId(user_id))
            can_water = tree_status.get("can_water_today", False)

            reason = (
                "ALREADY_WATERED_TODAY" if not can_water
                else "TOXIC_CONTENT" if journal.is_toxic
                else "NEGATIVE_EMOTION" if not is_positive
                else "NO_TEXT_CONTENT"
            )
            messages = {
                "ALREADY_WATERED_TODAY": "You have already watered your tree today",
                "TOXIC_CONTENT": "Cannot water tree with inappropriate content",
                "NEGATIVE_EMOTION": "Tree grows best with positive emotions",
                "NO_TEXT_CONTENT": "Please write something to water your tree"
            }
            tree_result = {
                "watered": False,
                "reason": reason,
                "message": messages.get(reason, "Cannot water tree at this time")
            }

        return {
            "id": str(journal.id),
            "created_at": journal.created_at.isoformat() + "Z",
            "emotion_label": journal.emotion_label or "Neutral",
            "text_content": journal.text_content or "",
            "sentiment_label": journal.sentiment_label,
            "sentiment_score": journal.sentiment_score or 0.0,
            "tags": journal.tags or [],
            "voice_note_path": journal.voice_note_path,
            "voice_text": journal.voice_text,
            "is_toxic": journal.is_toxic,
            "toxic_labels": journal.toxic_labels,
            "toxic_confidence": journal.toxic_confidence,
            "tree_watering_result": tree_result,
            "share_suggestion": share_suggestion
        }

    def _generate_positive_thoughts(self, emotion: str) -> List[str]:
        mapping = {
            "Happy": ["Today was a wonderful day", "I feel so grateful for everything"],
            "Excited": ["I'm full of energy!", "Great things are coming my way"],
            "Calm": ["I feel peaceful and balanced", "Everything is in harmony"],
            "Chill": ["I'm relaxed and content", "Taking it easy feels great"],
            "default": ["I took time to reflect on my feelings", "This is part of my growth journey"]
        }
        return mapping.get(emotion, mapping["default"])