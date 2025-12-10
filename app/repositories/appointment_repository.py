from fastapi import HTTPException, status
from app.models.appointment_model import Appointment
from app.models.expert_schedule_model import ExpertSchedule
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

class AppointmentRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["appointments"]
        self.schedule_collection = db["expert_schedules"]

    async def create_with_lock_slot(self, user_id: str, expert_profile_id: str, schedule_id: str, expert_price: int):
        session = await self.collection.database.client.start_session()
        try:
            async with session.start_transaction():
                schedule_doc = await self.schedule_collection.find_one_and_update(
                    {
                        "_id": ObjectId(schedule_id),
                        "expert_id": ObjectId(expert_profile_id),
                        "is_booked": False
                    },
                    {"$set": {"is_booked": True}},
                    return_document=True,
                    session=session
                )
                if not schedule_doc:
                    raise HTTPException(
                        status_code=400,
                        detail="Slot is already booked or does not exist"
                    )
                # Kiểm tra slot trong quá khứ
                slot_date = schedule_doc["date"]
                slot_start = schedule_doc["start_time"]
                now = datetime.now()
                slot_dt = datetime.strptime(f"{slot_date} {slot_start}", "%Y-%m-%d %H:%M")
                if slot_dt < now:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot book slot in the past"
                    )
                appointment_data = {
                    "user_id": ObjectId(user_id),
                    "expert_profile_id": ObjectId(expert_profile_id),
                    "schedule_id": ObjectId(schedule_id),
                    "appointment_date": schedule_doc["date"],
                    "start_time": schedule_doc["start_time"],
                    "end_time": schedule_doc["end_time"],
                    "price": expert_price,
                    "vat": int(expert_price * 0.1),
                    "total_amount": int(expert_price * 1.1),
                    "status": "pending",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                result = await self.collection.insert_one(appointment_data, session=session)
                appointment_data["_id"] = result.inserted_id
                return Appointment(**appointment_data), ExpertSchedule(**schedule_doc)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"System error, please try again: {str(e)}")
        finally:
            await session.end_session()

    async def get_by_id_for_user(self, appointment_id: str, user_id: str):
        doc = await self.collection.find_one({
            "_id": ObjectId(appointment_id),
            "user_id": ObjectId(user_id)
        })
        if not doc:
            return None
        # Fix for cancelled_by field: must be None or 'user'/'expert'
        if "cancelled_by" in doc and doc["cancelled_by"] not in (None, "user", "expert"):
            doc["cancelled_by"] = None
        return Appointment(**doc)

    async def get_list_by_user(self, user_id: str, status: str = None):
        query = {"user_id": ObjectId(user_id)}
        if status:
            if status not in ["pending", "upcoming", "past", "cancelled"]:
                raise HTTPException(status_code=400, detail="Invalid status")
            query["status"] = status
        cursor = self.collection.find(query).sort("appointment_date", -1)
        docs = await cursor.to_list(length=None)
        return [Appointment(**doc) for doc in docs]

    # === Expert queries ===
    async def get_by_expert_id(self, expert_profile_id: str, status: str = None):
        query = {"expert_profile_id": ObjectId(expert_profile_id)}
        if status:
            query["status"] = status
        cursor = self.collection.find(query).sort("appointment_date", 1)
        docs = await cursor.to_list(length=None)
        return [Appointment(**doc) for doc in docs]

    async def get_by_id_for_expert(self, appointment_id: str, expert_profile_id: str):
        doc = await self.collection.find_one({
            "_id": ObjectId(appointment_id),
            "expert_profile_id": ObjectId(expert_profile_id)
        })
        return Appointment(**doc) if doc else None

    # === TRANSACTION: ACCEPT ===
    async def accept_appointment_transaction(self, appointment: Appointment):
        session = await self.collection.database.client.start_session()
        try:
            async with session.start_transaction():
                now = datetime.utcnow()

                # 1. Update appointment
                await self.collection.update_one(
                    {"_id": appointment.id},
                    {"$set": {"status": "upcoming", "updated_at": now}},
                    session=session
                )

                # 2. Update wallet
                wallet_result = await self.collection.database["expert_wallets"].find_one_and_update(
                    {"expert_profile_id": appointment.expert_profile_id},  # Đổi tên field
                    {
                        "$inc": {
                            "total_earned": appointment.total_amount,
                            "balance": appointment.total_amount
                        },
                        "$set": {"updated_at": now}
                    },
                    upsert=True,
                    return_document=True,
                    session=session
                )

                # 3. Update profile total_patients
                update_result = await self.collection.database["expert_profiles"].update_one(
                    {"_id": appointment.expert_profile_id},
                    {"$inc": {"total_patients": 1}, "$set": {"updated_at": now}},
                    session=session
                )
                if update_result.modified_count == 0:
                    update_result = await self.collection.database["expert_profiles"].update_one(
                        {"_id": str(appointment.expert_profile_id)},
                        {"$inc": {"total_patients": 1}, "$set": {"updated_at": now}},
                        session=session
                    )

                return wallet_result
        finally:
            await session.end_session()

    # === TRANSACTION: DECLINE ===
    async def decline_appointment_transaction(self, appointment: Appointment, reason: str = None):
        session = await self.collection.database.client.start_session()
        try:
            async with session.start_transaction():
                now = datetime.utcnow()
                update_data = {
                    "status": "cancelled",
                    "cancelled_by": "expert",
                    "updated_at": now
                }
                if reason:
                    update_data["cancel_reason"] = reason

                await self.collection.update_one(
                    {"_id": appointment.id},
                    {"$set": update_data},
                    session=session
                )

                # Giải phóng slot
                await self.schedule_collection.update_one(
                    {"_id": appointment.schedule_id},
                    {"$set": {"is_booked": False}},
                    session=session
                )
        finally:
            await session.end_session()

    async def cancel_transaction(self, appointment: Appointment, reason: str):
            session = await self.collection.database.client.start_session()
            try:
                async with session.start_transaction():
                    now = datetime.utcnow()
                    update_data = {
                        "status": "cancelled",
                        "cancelled_by": "user",
                        "cancel_reason": reason,
                        "updated_at": now
                    }
                    await self.collection.update_one(
                        {"_id": appointment.id},
                        {"$set": update_data},
                        session=session
                    )

                    # Giải phóng slot
                    await self.schedule_collection.update_one(
                        {"_id": appointment.schedule_id},
                        {"$set": {"is_booked": False}},
                        session=session
                    )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"System error, please try again: {str(e)}")
            finally:
                await session.end_session()
                
    async def cancel_by_expert_transaction(self, appointment: Appointment, reason: str):
        session = await self.collection.database.client.start_session()
        try:
            async with session.start_transaction():
                now = datetime.utcnow()
                update_data = {
                    "status": "cancelled",
                    "cancelled_by": "expert",
                    "cancel_reason": reason,
                    "updated_at": now
                }
                await self.collection.update_one(
                    {"_id": appointment.id},
                    {"$set": update_data},
                    session=session
                )
                # Giải phóng slot
                await self.schedule_collection.update_one(
                    {"_id": appointment.schedule_id},
                    {"$set": {"is_booked": False}},
                    session=session
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"System error: {str(e)}")
        finally:
            await session.end_session()