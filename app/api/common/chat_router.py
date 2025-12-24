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


# NEW REST ENDPOINT: Mark chat as read khi mở từ list (offline → online)
@router.post("/chats/{chat_id}/read")
async def mark_chat_as_read(chat_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    """Mark all unread messages in a chat as read when user opens conversation from list"""
    chat_repo = ChatRepository(db)

    # Validate chat ownership
    chat_doc = await chat_repo.chats.find_one({"_id": ObjectId(chat_id)})
    if not chat_doc:
        raise HTTPException(status_code=404, detail="Chat not found")

    user_id_str = str(current_user["_id"])
    expert_profile_id = current_user.get("profile_id")
    is_user = str(chat_doc["user_id"]) == user_id_str
    is_expert = expert_profile_id and str(chat_doc["expert_profile_id"]) == expert_profile_id

    if not (is_user or is_expert):
        raise HTTPException(status_code=403, detail="Forbidden")

    role = "expert" if is_expert else "user"
    await chat_repo.mark_as_read(chat_id, role)

    return {"message": "Marked as read", "chat_id": chat_id}


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
    db_sender_id = ObjectId(expert_profile_id) if is_expert else ObjectId(user_id_str)

    # presence_id luôn là user_id_str (tracking)
    presence_id = user_id_str
    display_id = expert_profile_id if is_expert else user_id_str

    await websocket.accept()
    await manager.connect(websocket, chat_id, role, user_id_str)

    # Auto mark as read khi vào chat qua WebSocket
    try:
        await chat_repo.mark_as_read(chat_id, role)
    except Exception as e:
        logger.warning(f"Failed to auto mark as read on connect: {e}")

    presence_msg = {
        "event": "presence.join",
        "payload": {
            "role": role,
            "id": presence_id,
            "display_id": display_id,
            "user_id": user_id_str
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

                saved_msg = await chat_repo.save_message(
                    chat_id=chat_id,
                    sender_role=role,
                    sender_id=db_sender_id,
                    content=payload.content,
                    message_type=payload.message_type,
                    file_url=payload.file_url
                )

                broadcast_msg = {
                    "event": "message.new",
                    "payload": {
                        "id": str(saved_msg.id),
                        "sender_id": str(saved_msg.sender_id),
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

                    # Validate message tồn tại và thuộc chat này
                    message_doc = await chat_repo.messages.find_one({
                        "_id": ObjectId(payload.message_id),
                        "chat_id": ObjectId(chat_id)
                    })
                    if not message_doc:
                        await websocket.send_json({"event": "error", "payload": {"message": "Message not found"}})
                        continue

                    # Không cho mark tin của chính mình
                    if message_doc["sender_role"] == role:
                        await websocket.send_json({"event": "error", "payload": {"message": "Cannot mark own message as read"}})
                        continue

                    opponent_role = "expert" if role == "user" else "user"

                    # Mark tất cả tin chưa đọc đến message này
                    update_result = await chat_repo.messages.update_many(
                        {
                            "chat_id": ObjectId(chat_id),
                            "sender_role": opponent_role,
                            "created_at": {"$lte": message_doc["created_at"]},
                            "is_read": False
                        },
                        {"$set": {"is_read": True}}
                    )

                    # Recalculate unread count (an toàn với race condition)
                    unread_count = await chat_repo.messages.count_documents({
                        "chat_id": ObjectId(chat_id),
                        "sender_role": opponent_role,
                        "is_read": False
                    })

                    unread_field = "user_unread" if role == "user" else "expert_unread"
                    await chat_repo.chats.update_one(
                        {"_id": ObjectId(chat_id)},
                        {"$set": {unread_field: unread_count}}
                    )

                    # Broadcast với thông tin đầy đủ
                    await manager.broadcast({
                        "event": "messages.read",  # plural + thông tin chi tiết
                        "payload": {
                            "last_read_message_id": payload.message_id,
                            "count": update_result.modified_count,
                            "timestamp": message_doc["created_at"].isoformat()
                        }
                    }, chat_id, exclude=websocket)

                except Exception as e:
                    logger.error(f"Error handling message.read: {e}")
                    await websocket.send_json({"event": "error", "payload": {"message": "Failed to mark as read"}})

            elif msg.event == "presence.check":
                try:
                    if is_user:
                        partner_profile = await expert_repo.get_by_id(str(chat_doc["expert_profile_id"]))
                        if partner_profile:
                            partner_user_id = str(partner_profile.user_id)
                            partner_user = await user_repo.get_by_id(partner_user_id)
                            partner_online = manager.is_online(partner_user_id)
                            last_seen = partner_user.last_seen_at.isoformat() if partner_user and partner_user.last_seen_at else None
                        else:
                            partner_online = False
                            last_seen = None
                            partner_user_id = None
                    else:
                        partner_user_id = str(chat_doc["user_id"])
                        partner_user = await user_repo.get_by_id(partner_user_id)
                        partner_online = manager.is_online(partner_user_id)
                        last_seen = partner_user.last_seen_at.isoformat() if partner_user and partner_user.last_seen_at else None

                    await websocket.send_json({
                        "event": "presence.status",
                        "payload": {
                            "online": partner_online,
                            "partner_user_id": partner_user_id,
                            "last_seen_at": last_seen
                        }
                    })
                except Exception as e:
                    logger.error(f"Error checking presence: {e}")
                    await websocket.send_json({"event": "error", "payload": {"message": "Failed to check presence"}})

            else:
                await websocket.send_json({"event": "error", "payload": {"message": "Unsupported event"}})

    except WebSocketDisconnect:
        await manager.disconnect(websocket, chat_id, role, user_id_str)
        leave_msg = {
            "event": "presence.leave",
            "payload": {
                "role": role,
                "id": presence_id,
                "display_id": display_id,
                "user_id": user_id_str
            }
        }
        await manager.broadcast(leave_msg, chat_id)
    except Exception as e:
        logger.error(f"WS error: {e}")
        await manager.disconnect(websocket, chat_id, role, user_id_str)