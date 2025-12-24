from typing import List, Optional, Dict
from datetime import datetime, timezone, date
from bson import ObjectId
from app.services.user.user_tree_service import get_vn_now
 
from app.models.journal_model import Journal
from app.services.user.journal_service import JournalService
from app.services.user.user_tree_service import UserTreeService, AlreadyWateredTodayError
 
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
        journal_date: Optional[date]
    ) -> Dict:
        """
        Tạo journal + tưới cây tự động.
        - Nếu là nhật ký quá khứ → KHÔNG trả về field "created_at"
        - Nếu là nhật ký hôm nay hoặc không có journal_date → trả về "created_at" full datetime
        """
        # 1. TẠO JOURNAL
        journal = await self.journal_service.create_journal(
            user_id=user_id,
            emotion_label=emotion_label,
            text_content=text_content,
            voice_note_path=voice_note_path,
            voice_text=voice_text,
            tags=tags,
            journal_date=journal_date
        )

        # 2. KIỂM TRA ĐIỀU KIỆN TƯỚI CÂY
        tree_result = None
        share_suggestion = False

        is_positive = (
            journal.sentiment_label == "Positive" or
            (emotion_label and emotion_label in POSITIVE_EMOTIONS)
        )

        can_try_water = (
            not journal.is_toxic
            and text_content
            and text_content.strip()
            and is_positive
        )

        if can_try_water:
            try:
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

            except AlreadyWateredTodayError:
                tree_status = await self.tree_service.get_user_tree_status(ObjectId(user_id))
                tree_result = {
                    "watered": False,
                    "reason": "ALREADY_WATERED_TODAY",
                    "message": "You have already watered your tree today",
                    "can_water_today": tree_status.get("can_water_today", False)
                }
                share_suggestion = False

            except Exception as e:
                print(f"[ERROR] Unexpected error in nourish_tree: {e}")
                tree_status = await self.tree_service.get_user_tree_status(ObjectId(user_id))
                tree_result = {
                    "watered": False,
                    "reason": "ERROR",
                    "message": "Failed to water tree due to an error",
                    "can_water_today": tree_status.get("can_water_today", False)
                }
                share_suggestion = False
        else:
            tree_status = await self.tree_service.get_user_tree_status(ObjectId(user_id))
            can_water = tree_status.get("can_water_today", False)

            if journal.is_toxic:
                reason = "TOXIC_CONTENT"
                message = "Cannot water tree with inappropriate content"
            elif not is_positive:
                reason = "NEGATIVE_EMOTION"
                message = "Tree grows best with positive emotions"
            elif not text_content or not text_content.strip():
                reason = "NO_TEXT_CONTENT"
                message = "Please write something to water your tree"
            else:
                reason = "UNKNOWN"
                message = "Cannot water tree at this time"

            tree_result = {
                "watered": False,
                "reason": reason,
                "message": message,
                "can_water_today": can_water
            }
            share_suggestion = False

        # 6. TRẢ VỀ RESPONSE
        response: Dict = {
            "id": str(journal.id),
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

        # Chỉ thêm created_at nếu là nhật ký hôm nay hoặc không truyền journal_date
        if journal_date is None:
            is_today = True
        else:
            today_vn = get_vn_now().date()
            is_today = (journal_date == today_vn)

        if is_today:
            utc_created = journal.created_at.replace(tzinfo=timezone.utc)
            response["created_at"] = utc_created.isoformat()

        return response
 
    def _generate_positive_thoughts(self, emotion: str) -> List[str]:
        """Generate positive thoughts dựa trên emotion."""
        mapping = {
            "Happy": ["Today was a wonderful day", "I feel so grateful for everything"],
            "Excited": ["I'm full of energy!", "Great things are coming my way"],
            "Calm": ["I feel peaceful and balanced", "Everything is in harmony"],
            "Chill": ["I'm relaxed and content", "Taking it easy feels great"],
            "default": ["I took time to reflect on my feelings", "This is part of my growth journey"]
        }
        return mapping.get(emotion, mapping["default"])