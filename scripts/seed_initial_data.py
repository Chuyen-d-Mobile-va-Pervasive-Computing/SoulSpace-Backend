import asyncio
import os
import sys
import certifi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.core.config import settings

async def seed_data():
    client = AsyncIOMotorClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())
    db = client[settings.DATABASE_NAME]

    await db.positive_actions.insert_many([
        {"_id": ObjectId(), "action_name": "Uống nước", "description": "Uống 1 ly nước mỗi sáng."},
        {"_id": ObjectId(), "action_name": "Thiền", "description": "Thiền 5 phút để thư giãn."}
    ])

    await db.tests.insert_one({
        "_id": ObjectId(),
        "test_code": "PHQ-9",
        "test_name": "Patient Health Questionnaire",
        "description": "Đánh giá mức độ trầm cảm",
        "num_questions": 9,
        "severe_threshold": 15,
        "self_care_guidance": "Thử thiền 5 phút mỗi ngày",
        "expert_recommendation": "Liên hệ chuyên gia nếu cần",
        "image_url": "https://example.com/phq9.jpg"
    })

    print("Data seeded successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_data())