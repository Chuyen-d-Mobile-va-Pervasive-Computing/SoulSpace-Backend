# app/services/common/chat_service.py
from fastapi import HTTPException, status
from app.repositories.chat_repository import ChatRepository
from app.repositories.expert_repository import ExpertRepository
from app.repositories.user_repository import UserRepository
from app.models.expert_profile_model import ExpertProfile
from app.models.user_model import User
from app.core.ws_manager import manager
from bson import ObjectId
from datetime import datetime
from typing import List, Dict

class ChatService:
    def __init__(self, chat_repo: ChatRepository, expert_repo: ExpertRepository, user_repo: UserRepository):
        self.chat_repo = chat_repo
        self.expert_repo = expert_repo
        self.user_repo = user_repo

    async def start_chat(self, user_id: str, expert_profile_id: str) -> dict:
        expert = await self.expert_repo.get_by_id(expert_profile_id)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert profile not found")
        if expert.status != "approved":
            raise HTTPException(status_code=400, detail="Expert is not approved for chatting")
        chat = await self.chat_repo.get_or_create_chat(user_id, expert_profile_id)
        is_new = (datetime.utcnow() - chat.created_at).total_seconds() < 5
        return {
            "chat_id": str(chat.id),
            "expert": {
                "id": str(expert.id),
                "full_name": expert.full_name,
                "avatar_url": expert.avatar_url or ""
            },
            "created": is_new
        }

    async def get_conversations(self, current_user: dict) -> List[dict]:
        chats = []
        if current_user["role"] == "user":
            chats = await self.chat_repo.get_chats_by_user(str(current_user["_id"]))
        elif current_user["role"] == "expert" and "profile_id" in current_user:
            chats = await self.chat_repo.get_chats_by_expert(current_user["profile_id"])

        if not chats:
            return []

        result = []

        # Batch fetch để tránh N+1 query
        if current_user["role"] == "user":
            expert_profile_ids = [str(chat.expert_profile_id) for chat in chats]
            expert_profiles: Dict[str, ExpertProfile] = {}
            for pid in expert_profile_ids:
                profile = await self.expert_repo.get_by_id(pid)
                if profile:
                    expert_profiles[pid] = profile

            expert_user_ids = [str(p.user_id) for p in expert_profiles.values()]
            expert_users: Dict[str, User] = {}
            for uid in expert_user_ids:
                user = await self.user_repo.get_by_id(uid)
                if user:
                    expert_users[uid] = user
        else:
            user_ids = [str(chat.user_id) for chat in chats]
            users: Dict[str, User] = {}
            for uid in user_ids:
                user = await self.user_repo.get_by_id(uid)
                if user:
                    users[uid] = user

        for chat in chats:
            if current_user["role"] == "user":
                profile = expert_profiles.get(str(chat.expert_profile_id))
                if not profile:
                    continue
                partner_user = expert_users.get(str(profile.user_id))
                if not partner_user:
                    continue

                partner_id = str(chat.expert_profile_id)
                partner_name = profile.full_name
                partner_avatar = profile.avatar_url or ""
                partner_online = manager.is_online(str(profile.user_id))
                last_seen = partner_user.last_seen_at.isoformat() if not partner_online and partner_user.last_seen_at else None
                unread = chat.user_unread
            else:
                partner_user = users.get(str(chat.user_id))
                if not partner_user:
                    continue

                partner_id = str(chat.user_id)
                partner_name = getattr(partner_user, "username", "Anonymous User")
                partner_avatar = getattr(partner_user, "avatar_url", "")
                partner_online = manager.is_online(str(chat.user_id))
                last_seen = partner_user.last_seen_at.isoformat() if not partner_online and partner_user.last_seen_at else None
                unread = chat.expert_unread

            result.append({
                "chat_id": str(chat.id),
                "partner": {
                    "id": partner_id,
                    "full_name": partner_name,
                    "avatar_url": partner_avatar,
                    "online_status": partner_online,
                    "last_seen_at": last_seen
                },
                "last_message": chat.last_message or "",
                "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None,
                "unread_count": unread
            })

        # Sort newest first
        result.sort(key=lambda x: x.get("last_message_at") or "", reverse=True)
        return result

    async def get_messages(self, chat_id: str, current_user: dict) -> List[dict]:
        chat = await self.chat_repo.chats.find_one({"_id": ObjectId(chat_id)})
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        user_id = str(current_user["_id"])
        expert_profile_id = current_user.get("profile_id")

        if str(chat["user_id"]) != user_id and str(chat["expert_profile_id"]) != expert_profile_id:
            raise HTTPException(status_code=403, detail="You are not a participant of this chat")

        messages = await self.chat_repo.get_messages(chat_id)
        return [msg.dict(by_alias=True) for msg in messages]