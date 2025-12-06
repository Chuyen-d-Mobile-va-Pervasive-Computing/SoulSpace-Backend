from bson import ObjectId

class ChallengeRepository:
    def __init__(self, db):
        self.collection = db["challenges"]

    async def create(self, challenge_data: dict):
        result = await self.collection.insert_one(challenge_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def get(self, challenge_id: str):
        return await self.collection.find_one({"_id": ObjectId(challenge_id)})

    async def list(self):
        return await self.collection.find().to_list(length=100)

    async def update(self, challenge_id: str, update_data: dict):
        await self.collection.update_one(
            {"_id": ObjectId(challenge_id)},
            {"$set": update_data}
        )
        return await self.get(challenge_id)

    async def delete(self, challenge_id: str):
        return await self.collection.delete_one({"_id": ObjectId(challenge_id)})
