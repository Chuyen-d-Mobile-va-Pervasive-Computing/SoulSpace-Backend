from bson import ObjectId

class SensitiveKeywordRepository:
    def __init__(self, db):
        self.collection = db["sensitive_keywords"]

    async def create(self, keyword_data: dict):
        result = await self.collection.insert_one(keyword_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def get_all(self):
        return await self.collection.find().to_list(length=1000)

    async def get_by_severity(self, severity: str):
        return await self.collection.find({"severity": severity}).to_list(length=1000)

    async def get_by_category(self, category: str):
        return await self.collection.find({"category": category}).to_list(length=1000)

    async def delete(self, keyword_id: str):
        return await self.collection.delete_one({"_id": ObjectId(keyword_id)})

    async def update(self, keyword_id: str, update_data: dict):
        await self.collection.update_one(
            {"_id": ObjectId(keyword_id)},
            {"$set": update_data}
        )
        return await self.collection.find_one({"_id": ObjectId(keyword_id)})
