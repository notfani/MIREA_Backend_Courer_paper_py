from sqlalchemy.orm import Session
from models import User, Chat, Message
from schemas import UserCreate, ChatCreate, MessageCreate
from passlib.context import CryptContext
from encryption import encrypt_message
import logging

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger("crud")
logging.basicConfig(level=logging.DEBUG)

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    logger.debug(f"Попытка создания пользователя: {user.username}")
    if not user.password:
        logger.error("Пароль не может быть пустым.")
        raise ValueError("Пароль не может быть пустым.")

    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        logger.error("Пользователь с таким именем уже существует.")
        raise ValueError("Пользователь с таким именем уже существует.")

    hashed_password = pwd_context.hash(user.password)
    logger.debug("Пароль успешно захеширован.")
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.debug(f"Пользователь {user.username} успешно создан с ID {db_user.id}.")
    return db_user

def create_chat(db: Session, chat: ChatCreate, creator_id: int):
    db_chat = Chat(name=chat.name, is_group=chat.is_group)
    db.add(db_chat)
    db.flush()

    creator = db.query(User).filter(User.id == creator_id).first()
    db_chat.members.append(creator)

    for uid in chat.members:
        user = db.query(User).filter(User.id == uid).first()
        if user:
            db_chat.members.append(user)

    db.commit()
    db.refresh(db_chat)
    return db_chat

def add_user_to_chat(db: Session, chat_id: int, user_id: int):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if chat and user:
        chat.members.append(user)
        db.commit()

def get_user_chats(db: Session, user_id: int):
    return db.query(Chat).filter(Chat.members.any(id=user_id)).all()

def create_message(db: Session, message: MessageCreate, user_id: int):
    encrypted_content = encrypt_message(message.content)
    db_message = Message(content=encrypted_content, user_id=user_id, chat_id=message.chat_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages(db: Session, chat_id: int, skip: int = 0, limit: int = 60):
    messages = db.query(Message).filter(Message.chat_id == chat_id).offset(skip).limit(limit).all()
    from encryption import decrypt_message
    for msg in messages:
        msg.content = decrypt_message(msg.content)
    return messages