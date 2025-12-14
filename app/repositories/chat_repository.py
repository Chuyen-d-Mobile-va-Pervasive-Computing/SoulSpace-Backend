# app/repositories/chat_repository.py
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from app.models.chat_model import Chat
from app.models.chat_message_model import ChatMessage
from fastapi import HTTPException, status

class ChatRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.chats = db["chats"]
        self.messages = db["chat_messages"]

    async def get_or_create_chat(self, user_id: str, expert_profile_id: str) -> Chat:
        chat_doc = await self.chats.find_one({
            "user_id": ObjectId(user_id),
            "expert_profile_id": ObjectId(expert_profile_id)
        })
        if chat_doc:
            return Chat(**chat_doc)

        # Tạo mới
        insert_data = {
            "user_id": ObjectId(user_id),
            "expert_profile_id": ObjectId(expert_profile_id),
            "last_message": "",
            "last_message_at": None,
            "user_unread": 0,
            "expert_unread": 0,
            "created_at": datetime.utcnow()
        }
        result = await self.chats.insert_one(insert_data)
        insert_data["_id"] = result.inserted_id
        return Chat(**insert_data)

    async def save_message(self, chat_id: str, sender_role: str, sender_id: str, content: str, message_type: str = "text", file_url: str = None) -> ChatMessage:
        message_doc = {
            "chat_id": ObjectId(chat_id),
            "sender_role": sender_role,
            "sender_id": ObjectId(sender_id),
            "type": message_type,
            "content": content,
            "file_url": file_url,
            "is_read": False,
            "created_at": datetime.utcnow()
        }
        result = await self.messages.insert_one(message_doc)
        message_doc["_id"] = result.inserted_id

        # Update chat
        unread_field = "expert_unread" if sender_role == "user" else "user_unread"
        await self.chats.update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$set": {
                    "last_message": content[:100],
                    "last_message_at": datetime.utcnow()
                },
                "$inc": {unread_field: 1}
            }
        )
        return ChatMessage(**message_doc)

    async def get_messages(self, chat_id: str) -> List[ChatMessage]:
        cursor = self.messages.find({"chat_id": ObjectId(chat_id)}).sort("created_at", 1)
        docs = await cursor.to_list(length=None)
        return [ChatMessage(**doc) for doc in docs]

    async def get_chats_by_user(self, user_id: str) -> List[Chat]:
        cursor = self.chats.find({"user_id": ObjectId(user_id)})
        return [Chat(**doc) async for doc in cursor]

    async def get_chats_by_expert(self, expert_profile_id: str) -> List[Chat]:
        cursor = self.chats.find({"expert_profile_id": ObjectId(expert_profile_id)})
        return [Chat(**doc) async for doc in cursor]

    async def mark_as_read(self, chat_id: str, reader_role: str):
        unread_field = "user_unread" if reader_role == "expert" else "expert_unread"
        await self.chats.update_one(
            {"_id": ObjectId(chat_id)},
            {"$set": {unread_field: 0}}
        )
        # Mark messages from opponent as read
        opponent_role = "expert" if reader_role == "user" else "user"
        await self.messages.update_many(
            {"chat_id": ObjectId(chat_id), "sender_role": opponent_role},
            {"$set": {"is_read": True}}
        )
