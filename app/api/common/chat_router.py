# app/api/common/chat_router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from typing import Optional
from app.core.dependencies import get_current_user_ws, get_current_user
from app.repositories.chat_repository import ChatRepository
from app.repositories.expert_repository import ExpertRepository
from app.repositories.user_repository import UserRepository
from app.services.common.chat_service import ChatService
from app.schemas.common.chat_schema import WebSocketMessage, MessageSendPayload, TypingPayload, ReadReceiptPayload
from app.core.ws_manager import manager
from app.core.database import get_db
from bson import ObjectId
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Realtime Chat"])

@router.get("/chats")
async def get_chats(current_user=Depends(get_current_user), db=Depends(get_db)):
    chat_repo = ChatRepository(db)
    expert_repo = ExpertRepository(db)
    user_repo = UserRepository(db)
    service = ChatService(chat_repo, expert_repo, user_repo)
    try:
        conversations = await service.get_conversations(current_user)
        return {"data": conversations}
    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")

@router.get("/chats/{chat_id}/messages")
async def get_messages(chat_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    chat_repo = ChatRepository(db)
    service = ChatService(chat_repo, ExpertRepository(db), UserRepository(db))
    try:
        messages = await service.get_messages(chat_id, current_user)
        return {"messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch messages")

@router.post("/start/{expert_profile_id}")
async def start_chat(expert_profile_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    if current_user["role"] != "user":
        raise HTTPException(status_code=403, detail="Only users can start a chat")
    chat_repo = ChatRepository(db)
    expert_repo = ExpertRepository(db)
    user_repo = UserRepository(db)
    service = ChatService(chat_repo, expert_repo, user_repo)
    try:
        result = await service.start_chat(str(current_user["_id"]), expert_profile_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start chat")

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str, token: Optional[str] = Query(None)):
    current_user = await get_current_user_ws(websocket, token)
    if not current_user:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    db = websocket.app.state.db
    chat_repo = ChatRepository(db)
    expert_repo = ExpertRepository(db)
    user_repo = UserRepository(db)

    if not hasattr(manager, "user_repo") or manager.user_repo is None:
        manager.set_user_repo(user_repo)

    chat_doc = await chat_repo.chats.find_one({"_id": ObjectId(chat_id)})
    if not chat_doc:
        await websocket.close(code=1008, reason="Chat not found")
        return

    user_id_str = str(current_user["_id"])
    expert_profile_id = current_user.get("profile_id")
    is_user = str(chat_doc["user_id"]) == user_id_str
    is_expert = expert_profile_id and str(chat_doc["expert_profile_id"]) == expert_profile_id

    if not (is_user or is_expert):
        await websocket.close(code=1008, reason="Forbidden")
        return

    if is_expert:
        expert = await expert_repo.get_by_id(expert_profile_id)
        if not expert or expert.status != "approved":
            await websocket.close(code=1008, reason="Expert not approved")
            return

    role = "expert" if is_expert else "user"
    # Định danh đúng cho database
    db_sender_id = ObjectId(expert_profile_id) if is_expert else ObjectId(user_id_str)
    # Định danh cho presence và broadcast
    presence_id = expert_profile_id if is_expert else user_id_str

    await websocket.accept()

    await manager.connect(websocket, chat_id, role, user_id_str)

    await chat_repo.mark_as_read(chat_id, role)

    presence_msg = {
        "event": "presence.join",
        "payload": {
            "role": role,
            "id": presence_id
        }
    }
    await manager.broadcast(presence_msg, chat_id, exclude=websocket)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                raw_msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"event": "error", "payload": {"message": "Invalid JSON"}})
                continue

            event = raw_msg.get("event")

            if event == "ping":
                await websocket.send_json({"event": "pong"})
                continue

            try:
                msg = WebSocketMessage(**raw_msg)
            except ValueError:
                await websocket.send_json({"event": "error", "payload": {"message": "Invalid message format"}})
                continue

            if msg.event == "message.send":
                try:
                    payload = MessageSendPayload(**msg.payload)
                    if not payload.content.strip():
                        await websocket.send_json({"event": "error", "payload": {"message": "Empty message"}})
                        continue
                except ValueError:
                    await websocket.send_json({"event": "error", "payload": {"message": "Invalid payload"}})
                    continue

                # FIX: Dùng db_sender_id đúng (ObjectId)
                saved_msg = await chat_repo.save_message(
                    chat_id=chat_id,
                    sender_role=role,
                    sender_id=db_sender_id,  # ĐÃ SỬA
                    content=payload.content,
                    message_type=payload.message_type,
                    file_url=payload.file_url
                )

                broadcast_msg = {
                    "event": "message.new",
                    "payload": {
                        "id": str(saved_msg.id),
                        "sender_id": str(db_sender_id),  # ĐÃ SỬA: string của ObjectId
                        "sender_role": role,
                        "content": payload.content,
                        "type": payload.message_type,
                        "file_url": payload.file_url,
                        "created_at": saved_msg.created_at.isoformat(),
                        "is_read": False
                    }
                }
                await manager.broadcast(broadcast_msg, chat_id, exclude=websocket)

            elif msg.event in ["typing.start", "typing.stop"]:
                try:
                    payload = TypingPayload(**msg.payload)
                    await manager.broadcast({
                        "event": msg.event,
                        "payload": {"is_typing": payload.is_typing}
                    }, chat_id, exclude=websocket)
                except ValueError:
                    await websocket.send_json({"event": "error", "payload": {"message": "Invalid typing payload"}})

            elif msg.event == "message.read":
                try:
                    payload = ReadReceiptPayload(**msg.payload)
                    await chat_repo.messages.update_one(
                        {"_id": ObjectId(payload.message_id)},
                        {"$set": {"is_read": True}}
                    )
                    await manager.broadcast({
                        "event": "message.read",
                        "payload": {"message_id": payload.message_id}
                    }, chat_id, exclude=websocket)
                except ValueError:
                    await websocket.send_json({"event": "error", "payload": {"message": "Invalid read payload"}})

            else:
                await websocket.send_json({"event": "error", "payload": {"message": "Unsupported event"}})

    except WebSocketDisconnect:
        await manager.disconnect(websocket, chat_id, role, user_id_str)
        leave_msg = {
            "event": "presence.leave",
            "payload": {
                "role": role,
                "id": presence_id
            }
        }
        await manager.broadcast(leave_msg, chat_id)
    except Exception as e:
        logger.error(f"WS error: {e}")
        await manager.disconnect(websocket, chat_id, role, user_id_str)