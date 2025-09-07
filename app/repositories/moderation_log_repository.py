from datetime import datetime

class ModerationLogRepository:
    def __init__(self, db):
        self.collection = db["moderation_logs"]

    async def create_log(self, content_id, content_type, user_id, text, detected_keywords, action):
        log = {
            "content_id": content_id,
            "content_type": content_type,
            "user_id": user_id,
            "text": text,
            "detected_keywords": detected_keywords,
            "action": action,
            "created_at": datetime.utcnow(),
        }
        await self.collection.insert_one(log)
        return log