import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import logging # Оставляем импорт для других частей, но для вывода используем print

logging.basicConfig(level=logging.INFO) # Можно удалить, если не используется, но оставим на всякий случай
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: str):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)
        print(f"WebSocket connected to chat {chat_id}. Total connections for this chat: {len(self.active_connections[chat_id])}", flush=True)

    def disconnect(self, websocket: WebSocket, chat_id: str):
        if chat_id in self.active_connections:
            self.active_connections[chat_id].remove(websocket)
            print(f"WebSocket disconnected from chat {chat_id}.", flush=True)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]
                print(f"No more connections for chat {chat_id}, removing from manager.", flush=True)

    async def broadcast_to_chat(self, message: str, chat_id: str):
        if chat_id in self.active_connections:
            connections = self.active_connections[chat_id]
            print(f"Broadcasting to {len(connections)} connection(s) in chat {chat_id}", flush=True)
            # Итерируемся по копии списка, чтобы можно было безопасно удалять элементы из оригинала
            for connection in list(connections):
                try:
                    await connection.send_text(message)
                except (RuntimeError, WebSocketDisconnect):
                    print(f"Failed to send to a closed connection (RuntimeError or WebSocketDisconnect). Removing it.", flush=True)
                    connections.remove(connection)
        else:
            print(f"No active connections found for chat {chat_id} to broadcast to.", flush=True)

manager = ConnectionManager()

async def handle_websocket(websocket: WebSocket, chat_id: str, user_id: int):
    await manager.connect(websocket, chat_id)
    try:
        await asyncio.Future()
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
        print(f"User {user_id} disconnected from chat {chat_id}.", flush=True)
    except Exception as e:
        print(f"Error in websocket for chat {chat_id}: {e}", flush=True)
        manager.disconnect(websocket, chat_id)