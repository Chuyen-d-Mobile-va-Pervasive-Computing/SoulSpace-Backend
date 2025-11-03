from fastapi import HTTPException, status
from app.models.user_model import User
from bson import ObjectId
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase 
class UserRepository:
    def __init__(self,  db: AsyncIOMotorDatabase):
        self.db = db

    async def create(self, user: User) -> User:
        try:
            user_data_to_insert = {
                "_id": user.id,
                "username": user.username,
                "email": user.email,
                "password": user.password,
                "role": user.role,
                "created_at": user.created_at,
                "last_login_at": user.last_login_at,
                "total_points": user.total_points,
                "reset_otp": user.reset_otp,
                "reset_otp_expiry": user.reset_otp_expiry,
            }
            
            result = await self.db.users.insert_one(user_data_to_insert)
            user.id = result.inserted_id
            return user
        except Exception as e:
            if "duplicate key" in str(e):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already exists")
                
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create user: {str(e)}")
        
    async def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            user_data = await self.db.users.find_one({"_id": ObjectId(user_id)})
            return User(**user_data) if user_data else None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch user: {str(e)}")

    async def get_by_email(self, email: str) -> Optional[User]:
        try:
            user_data = await self.db.users.find_one({"email": email})
            return User(**user_data) if user_data else None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch user: {str(e)}")

    async def get_by_username(self, username: str) -> Optional[User]:
        try:
            user_data = await self.db.users.find_one({"username": username})
            return User(**user_data) if user_data else None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch user by username: {str(e)}")

    async def update(self, user_id: str, update_data: dict):
        try:
            await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update user: {str(e)}")

    async def delete(self, user_id: str):
        try:
            await self.db.users.delete_one({"_id": ObjectId(user_id)})
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete user: {str(e)}")

    async def update_last_login(self, user_id: str, login_time: datetime):
        try:
            await self.update(user_id, {"last_login_at": login_time})
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update last login: {str(e)}")

    async def update_reset_otp(self, user_id: str, otp: str, expiry: datetime):
        try:
            await self.update(user_id, {"reset_otp": otp, "reset_otp_expiry": expiry})
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update reset OTP: {str(e)}")

    async def clear_reset_otp(self, user_id: str):
        try:
            await self.update(user_id, {"reset_otp": None, "reset_otp_expiry": None})
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to clear reset OTP: {str(e)}")
        
    async def increment_total_points(self, user_id: ObjectId, points_to_add: int) -> bool:
        try:
            result = await self.db.users.update_one(
                {"_id": user_id},
                {"$inc": {"total_points": points_to_add}}
            )
            return result.modified_count > 0
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Failed to increment user points: {str(e)}"
            )