import asyncio
import websockets
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
from redis_client import cache_message, publish_notification
from encryption import encrypt_message, decrypt_message

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast_to_chat(self, message: str, chat_id: str):
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                await connection.send_text(message)

    async def notify_user(self, user_id: int, message: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(f"NOTIFICATION: {message}")

manager = ConnectionManager()

async def handle_websocket(websocket: WebSocket, chat_id: str, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            encrypted_data = encrypt_message(data)
            cache_message(chat_id, {"content": encrypted_data, "user_id": user_id})
            await manager.broadcast_to_chat(encrypted_data, chat_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)