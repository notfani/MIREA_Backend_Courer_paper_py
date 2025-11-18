from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class ChatCreate(BaseModel):
    name: str
    is_group: bool = False
    members: List[int]

class Chat(BaseModel):
    id: int
    name: str
    is_group: bool
    created_at: datetime
    members: List[User]

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str
    chat_id: int

class Message(BaseModel):
    id: int
    content: str
    timestamp: datetime
    user_id: int
    chat_id: int
    user: User

    class Config:
        from_attributes = True