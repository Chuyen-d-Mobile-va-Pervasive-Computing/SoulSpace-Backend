from app.models.expert_wallet_model import ExpertWallet
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

class ExpertWalletRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["expert_wallets"]

    async def get_by_expert_id(self, expert_profile_id: str) -> Optional[ExpertWallet]:
        doc = await self.collection.find_one({"expert_profile_id": ObjectId(expert_profile_id)})
        return ExpertWallet(**doc) if doc else None