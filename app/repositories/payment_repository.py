from fastapi import HTTPException, status
from app.models.payment_model import Payment
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

class PaymentRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["payments"]

    async def get_latest_by_appointment(self, appointment_id: str):
        doc = await self.collection.find_one(
            {"appointment_id": ObjectId(appointment_id)},
            sort=[("created_at", -1)]
        )
        return Payment(**doc) if doc else None

    async def create_payment(self, appointment, method: str, status: str):
        payment_data = {
            "appointment_id": appointment.id,
            "user_id": appointment.user_id,
            "expert_profile_id": appointment.expert_profile_id, 
            "method": method,
            "amount": appointment.total_amount,
            "status": status,
            "paid_at": datetime.utcnow() if status == "paid" else None,
            "created_at": datetime.utcnow()
        }
        result = await self.collection.insert_one(payment_data)
        payment_data["_id"] = result.inserted_id
        return Payment(**payment_data)

    async def update_status(self, payment_id: str, new_status: str):
        try:
            update_data = {"status": new_status}
            if new_status == "refunded":
                update_data["refunded_at"] = datetime.utcnow()
            await self.collection.update_one(
                {"_id": ObjectId(payment_id)},
                {"$set": update_data}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update payment status: {str(e)}")

async def update_status(self, payment_id: str, new_status: str):
        try:
            update_data = {"status": new_status}
            if new_status == "refunded":
                update_data["refunded_at"] = datetime.utcnow()  # Thêm trường nếu cần
            await self.collection.update_one(
                {"_id": ObjectId(payment_id)},
                {"$set": update_data}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update payment status: {str(e)}")