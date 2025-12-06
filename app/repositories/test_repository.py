from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Optional, List
from app.models.test_model import Test

class TestRepository:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection = database["tests"]

    async def get_all_tests(self) -> List[dict]:
        # Chỉ trả về test chưa xóa mềm
        return await self.collection.find({"is_deleted": False}).to_list(length=None)

    async def get_test_by_id(self, test_id: ObjectId) -> Optional[dict]:
        return await self.collection.find_one({"_id": ObjectId(test_id)})

    async def get_test_by_code(self, test_code: str) -> Optional[dict]:
        return await self.collection.find_one({"test_code": test_code})

    async def create_test(self, test_data: dict) -> str:
        # Tự động thêm trường is_deleted: False nếu chưa có
        test_data.setdefault("is_deleted", False)
        result = await self.collection.insert_one(test_data)
        return str(result.inserted_id)

    async def update_test(self, test_id: ObjectId, update_data: dict) -> bool:
        result = await self.collection.update_one({"_id": ObjectId(test_id)}, {"$set": update_data})
        return result.modified_count > 0

    async def soft_delete_test(self, test_id: ObjectId) -> bool:
        result = await self.collection.update_one({"_id": ObjectId(test_id)}, {"$set": {"is_deleted": True}})
        return result.modified_count > 0

    async def is_test_code_unique(self, test_code: str) -> bool:
        return await self.collection.count_documents({"test_code": test_code}) == 0