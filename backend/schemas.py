from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

    @validator("username")
    def validate_username(cls, value):
        if len(value) < 3:
            raise ValueError("Имя пользователя должно быть не менее 3 символов.")
        return value

    @validator("password")
    def validate_password(cls, value):
        if len(value) < 6:
            raise ValueError("Пароль должен быть не менее 6 символов.")
        return value

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