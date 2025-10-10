from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.journal_model import Journal
from bson import ObjectId

class JournalRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.get_collection("journals")
        self.collection.create_index([("user_id", 1), ("created_at", -1)])
        self.collection.create_index("tags")  # Index for List[str]

    async def create(self, journal: dict) -> Journal:
        result = await self.collection.insert_one(journal)
        journal["_id"] = result.inserted_id
        return Journal(**journal)

    async def get_by_user(self, user_id: str) -> list[Journal]:
        cursor = self.collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)
        return [Journal(**doc) async for doc in cursor]