from sqlalchemy.orm import Session
from models import User, Chat, Message
from schemas import UserCreate, ChatCreate, MessageCreate
from passlib.context import CryptContext
from encryption import encrypt_message
import logging

# Настраиваем контекст паролей с явными параметрами
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)

logger = logging.getLogger(__name__)

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    logger.info(f"Attempting to create user: {user.username}")
    logger.info(f"Password length: {len(user.password)} chars, {len(user.password.encode('utf-8'))} bytes")

    # Проверяем существование пользователя
    existing_user = get_user_by_username(db, user.username)
    if existing_user:
        logger.warning(f"User already exists: {user.username}")
        raise ValueError("User already exists")

    # Проверяем длину пароля
    password_bytes = user.password.encode('utf-8')
    if len(password_bytes) > 72:
        logger.error(f"Password too long: {len(password_bytes)} bytes")
        raise ValueError("Password is too long (max 72 bytes)")

    # Если пароль слишком длинный для bcrypt, обрезаем его
    password_to_hash = user.password
    if len(password_bytes) > 72:
        password_to_hash = user.password[:72]
        logger.warning(f"Password truncated to 72 bytes")

    logger.info("Hashing password...")
    try:
        hashed_password = pwd_context.hash(password_to_hash)
        logger.info("Password hashed successfully")
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        # Пробуем альтернативный подход
        try:
            import bcrypt
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_to_hash.encode('utf-8'), salt).decode('utf-8')
            logger.info("Password hashed using direct bcrypt")
        except Exception as e2:
            logger.error(f"Alternative hashing also failed: {e2}")
            raise ValueError(f"Cannot hash password: {str(e)}")

    logger.info("Creating user in database...")
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created successfully with id: {db_user.id}")
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