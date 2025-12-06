from datetime import datetime
from typing import Optional, List, Union
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.expert_profile_model import ExpertProfile


class ExpertRepository:
    """Repository for expert profile data operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["expert_profiles"]
        print("🗄️ ExpertRepository initialized")
        print(f"   Database: {db.name}")
        print(f"   Collection: expert_profiles")

    async def create(self, profile_data: Union[ExpertProfile, dict]) -> ExpertProfile:
        """Create new expert profile (store ObjectId, return model)"""
        doc = (
            profile_data.model_dump(by_alias=True)
            if isinstance(profile_data, ExpertProfile)
            else profile_data
        )

        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return ExpertProfile(**doc)

    async def get_by_id(self, profile_id: str) -> Optional[ExpertProfile]:
        """Get expert profile by ID - supports ObjectId or legacy string IDs"""
        # Try ObjectId query first
        doc = None
        try:
            doc = await self.collection.find_one({"_id": ObjectId(profile_id)})
        except Exception:
            doc = None

        # Fallback to plain string _id (legacy data)
        if not doc:
            doc = await self.collection.find_one({"_id": profile_id})

        return ExpertProfile(**doc) if doc else None

    async def get_by_user_id(self, user_id: str) -> Optional[ExpertProfile]:
        """Get expert profile by user_id (ObjectId-first, fallback string)"""
        doc = None
        try:
            doc = await self.collection.find_one({"user_id": ObjectId(user_id)})
        except Exception:
            doc = None

        if not doc:
            doc = await self.collection.find_one({"user_id": user_id})

        return ExpertProfile(**doc) if doc else None

    async def get_by_status(self, status: str) -> List[ExpertProfile]:
        """Get all profiles with given status"""
        cursor = self.collection.find({"status": status})
        docs = await cursor.to_list(length=None)
        return [ExpertProfile(**doc) for doc in docs]

    async def get_all(self, status: Optional[str] = None) -> List[ExpertProfile]:
        """Get all expert profiles, optionally filtered by status"""
        query = {"status": status} if status else {}
        cursor = self.collection.find(query)
        docs = await cursor.to_list(length=None)
        return [ExpertProfile(**doc) for doc in docs]

    async def update(self, profile_id: str, update_data: dict) -> Optional[ExpertProfile]:
        """Update expert profile - handles ObjectId and legacy string IDs"""
        result = None
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(profile_id)},
                {"$set": update_data},
                return_document=True
            )
        except Exception:
            result = None

        if not result:
            result = await self.collection.find_one_and_update(
                {"_id": profile_id},
                {"$set": update_data},
                return_document=True
            )

        return ExpertProfile(**result) if result else None

    async def delete(self, profile_id: str) -> bool:
        """Delete expert profile (ObjectId-first, fallback string)"""
        result = None
        try:
            result = await self.collection.delete_one({"_id": ObjectId(profile_id)})
        except Exception:
            result = None

        if not result or result.deleted_count == 0:
            result = await self.collection.delete_one({"_id": profile_id})

        return result.deleted_count > 0 if result else False
