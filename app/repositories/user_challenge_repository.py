from bson import ObjectId
from datetime import datetime

class UserChallengeRepository:
    def __init__(self, db):
        self.collection = db["user_challenges"]

    async def create(self, user_challenge_data: dict):
        result = await self.collection.insert_one(user_challenge_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def get(self, user_challenge_id: str):
        return await self.collection.find_one({"_id": ObjectId(user_challenge_id)})

    async def get_by_user_and_challenge(self, user_id: str, challenge_id: str):
        return await self.collection.find_one({
            "user_id": user_id,
            "challenge_id": ObjectId(challenge_id)
        })

    async def list_by_user(self, user_id: str):
        return await self.collection.find({"user_id": user_id}).to_list(length=100)

    async def update_progress(self, user_challenge_id: str, progress: int, earned_points: int):
        await self.collection.update_one(
            {"_id": ObjectId(user_challenge_id)},
            {
                "$set": {
                    "progress": progress,
                    "earned_points": earned_points,
                    "last_action_at": datetime.utcnow()
                }
            }
        )
        return await self.get(user_challenge_id)

    async def add_badge(self, user_challenge_id: str, badge_data: dict):
        await self.collection.update_one(
            {"_id": ObjectId(user_challenge_id)},
            {"$push": {"badges": badge_data}}
        )
        return await self.get(user_challenge_id)
