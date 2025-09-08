from fastapi import HTTPException, status
from app.models.user_model import User
from bson import ObjectId
from datetime import datetime
from typing import Optional

class UserRepository:
    def __init__(self, db):
        self.db = db

    async def create(self, user: User) -> User:
        try:
            result = await self.db.users.insert_one(user.dict(by_alias=True))
            user.id = result.inserted_id
            return user
        except Exception as e:
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