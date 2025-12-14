# app/core/ws_manager.py
from fastapi import WebSocket
from typing import Dict, Set, Optional
from datetime import datetime
from app.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, Set[WebSocket]]] = {}
        self.connection_count: Dict[str, int] = {}
        
    def is_online(self, user_id: str) -> bool:
        return user_id in self.connection_count and self.connection_count[user_id] > 0

    def set_user_repo(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def connect(self, websocket: WebSocket, chat_id: str, role: str, user_id: str):
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = {"user": set(), "expert": set()}
        self.active_connections[chat_id][role].add(websocket)

        old_count = self.connection_count.get(user_id, 0)
        self.connection_count[user_id] = old_count + 1

        if old_count == 0 and self.user_repo:
            try:
                await self.user_repo.update(
                    user_id,
                    {
                        "online_status": True,
                        "last_seen_at": None
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to set online for user {user_id}: {e}")

    async def disconnect(self, websocket: WebSocket, chat_id: str, role: str, user_id: str):
        if chat_id in self.active_connections and role in self.active_connections[chat_id]:
            self.active_connections[chat_id][role].discard(websocket)
            if not any(self.active_connections[chat_id].values()):
                del self.active_connections[chat_id]

        if user_id in self.connection_count:
            self.connection_count[user_id] -= 1
            if self.connection_count[user_id] <= 0:
                del self.connection_count[user_id]
                try:
                    await self.user_repo.update(
                        user_id,
                        {
                            "online_status": False,
                            "last_seen_at": datetime.utcnow()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to persist last_seen_at for user {user_id}: {e}")

    async def broadcast(self, message: dict, chat_id: str, exclude: Optional[WebSocket] = None):
        if chat_id not in self.active_connections:
            return
        dead = []
        for sockets in self.active_connections[chat_id].values():
            for ws in sockets:
                if ws == exclude:
                    continue
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
        for ws in dead:
            for role_sockets in self.active_connections[chat_id].values():
                role_sockets.discard(ws)

manager = ConnectionManager()