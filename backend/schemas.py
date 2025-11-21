from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=72)

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long (max 72 bytes)')
        return v

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