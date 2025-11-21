from fastapi import FastAPI, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base
import models
from schemas import UserCreate, MessageCreate, ChatCreate
from crud import create_user, create_message, get_messages, create_chat, get_user_chats, add_user_to_chat
from auth import get_current_user, authenticate_user, create_access_token, get_db
from websocket import handle_websocket
from redis_client import get_online_users, publish_notification

from prometheus_client import make_asgi_app, Counter, Histogram
import time
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Метрики
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_TIME = Histogram('http_request_duration_seconds', 'Duration of HTTP requests', ['method', 'endpoint'])

app = FastAPI()

# Подключаем Prometheus middleware
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Промежуточное ПО для сбора метрик
@app.middleware("http")
async def add_prometheus_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_TIME.labels(method=request.method, endpoint=request.url.path).observe(time.time() - start_time)
    return response

# Создание таблиц с обработкой race condition
try:
    Base.metadata.create_all(bind=engine)
except IntegrityError:
    # Таблицы уже созданы другим инстансом
    pass

@app.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user)
    return {"message": "User registered", "user_id": db_user.id}

@app.post("/token")
def login(user: UserCreate, db: Session = Depends(get_db)):
    user_db = authenticate_user(db, user.username, user.password)
    if not user_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_access_token(data={"sub": user_db.username}), "token_type": "bearer"}

@app.post("/chats/")
def create_new_chat(chat: ChatCreate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    new_chat = create_chat(db, chat, current_user.id)
    for member_id in chat.members:
        publish_notification(member_id, f"Вы были добавлены в чат '{new_chat.name}'")
    return new_chat

@app.get("/chats/")
def read_user_chats(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = get_user_chats(db, current_user.id)
    return chats

@app.post("/chats/{chat_id}/add-user/{user_id}")
def add_user_to_group(chat_id: int, user_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    add_user_to_chat(db, chat_id, user_id)
    publish_notification(user_id, f"Вас добавили в чат {chat_id}")
    return {"message": f"User {user_id} added to chat {chat_id}"}

@app.post("/messages/")
def send_message(msg: MessageCreate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    message = create_message(db, msg, current_user.id)
    chat = db.query(models.Chat).filter(models.Chat.id == msg.chat_id).first()
    for member in chat.members:
        if member.id != current_user.id:
            publish_notification(member.id, f"Новое сообщение в '{chat.name}'")
    return message

@app.get("/messages/{chat_id}")
def read_messages(chat_id: int, skip: int = 0, limit: int = 60, db: Session = Depends(get_db)):
    messages = get_messages(db, chat_id, skip=skip, limit=limit)
    return messages

@app.get("/online-users/")
def online_users():
    return get_online_users()

@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str, current_user = Depends(get_current_user)):
    await handle_websocket(websocket, chat_id, current_user.id)