from fastapi import FastAPI, Depends, HTTPException, WebSocket, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base
import models
from schemas import UserCreate, MessageCreate, ChatCreate
from crud import create_user, create_message, get_messages, create_chat, get_user_chats, add_user_to_chat
from auth import get_current_user, authenticate_user, create_access_token, get_db, get_current_user_ws
from websocket import handle_websocket, manager
from redis_client import get_online_users
import json

from prometheus_client import make_asgi_app, Counter, Histogram
import time
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordRequestForm
from starlette.websockets import WebSocketDisconnect

# Загружаем переменные окружения из .env файла
load_dotenv()

# Метрики
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_TIME = Histogram('http_request_duration_seconds', 'Duration of HTTP requests', ['method', 'endpoint'])

app = FastAPI(root_path="/api")

# Обработчик ошибок валидации
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Извлекаем первую ошибку для более понятного сообщения
    if errors:
        first_error = errors[0]
        field = first_error.get('loc', ['unknown'])[-1]
        msg = first_error.get('msg', 'Validation error')

        # Формируем понятное сообщение
        if 'min_length' in msg.lower():
            return JSONResponse(
                status_code=422,
                content={"detail": f"{field} слишком короткий"}
            )
        elif 'max_length' in msg.lower():
            return JSONResponse(
                status_code=422,
                content={"detail": f"{field} слишком длинный"}
            )
        else:
            return JSONResponse(
                status_code=422,
                content={"detail": msg}
            )

    return JSONResponse(
        status_code=422,
        content={"detail": "Ошибка валидации данных"}
    )

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
    Base.metadata.create_all(bind=engine, checkfirst=True)
except IntegrityError:
    # Таблицы уже созданы другим инстансом
    pass

@app.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "User registered", "user_id": db_user.id}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info(f"Login attempt for user: {form_data.username}")
    logger.info(f"Form data received - username: {form_data.username}, password length: {len(form_data.password) if form_data.password else 0}")

    user_db = authenticate_user(db, form_data.username, form_data.password)
    if not user_db:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user_db.username})
    logger.info(f"User logged in successfully: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/chats/")
def create_new_chat(chat: ChatCreate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    new_chat = create_chat(db, chat, current_user.id)
    return new_chat

@app.get("/chats/")
def read_user_chats(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = get_user_chats(db, current_user.id)
    return chats

@app.get("/chats/{chat_id}")
def get_chat_details(chat_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    # Проверяем, что пользователь является участником чата
    if current_user not in chat.members:
        raise HTTPException(status_code=403, detail="Access denied")
    return chat

@app.get("/users/")
def get_all_users(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [{"id": user.id, "username": user.username} for user in users]

@app.post("/chats/{chat_id}/add-user/{user_id}")
def add_user_to_group(chat_id: int, user_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    # Проверяем, что чат существует и это групповой чат
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Проверяем, что текущий пользователь является участником чата
    if current_user not in chat.members:
        raise HTTPException(status_code=403, detail="Access denied")

    # Проверяем, что добавляемый пользователь существует
    user_to_add = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем, что пользователь еще не в чате
    if user_to_add in chat.members:
        raise HTTPException(status_code=400, detail="User already in chat")

    add_user_to_chat(db, chat_id, user_id)
    return {"message": f"User {user_to_add.username} added to chat {chat.name}"}

@app.get("/chats/{chat_id}/members")
async def get_chat_members(chat_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получить список участников чата"""
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Проверяем, что текущий пользователь является участником чата
    if current_user not in chat.members:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    return [{"id": user.id, "username": user.username} for user in chat.members]

@app.post("/chats/{chat_id}/members")
async def add_chat_member(chat_id: int, data: dict, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Добавить участника в чат по username"""
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Проверяем, что текущий пользователь является участником чата
    if current_user not in chat.members:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    username = data.get("username")
    user_to_add = db.query(models.User).filter(models.User.username == username).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем, что пользователь еще не в чате
    if user_to_add in chat.members:
        raise HTTPException(status_code=400, detail="User already in chat")

    add_user_to_chat(db, chat_id, user_to_add.id)
    return {"message": f"User {user_to_add.username} added to chat {chat.name}"}

@app.delete("/chats/{chat_id}/members/{username}")
async def remove_chat_member(chat_id: int, username: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Удалить участника из чата"""
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Проверяем, что текущий пользователь является участником чата
    if current_user not in chat.members:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    user_to_remove = db.query(models.User).filter(models.User.username == username).first()
    if not user_to_remove:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем, что пользователь в чате
    if user_to_remove not in chat.members:
        raise HTTPException(status_code=400, detail="User is not in this chat")

    # Удаляем пользователя из чата
    chat.members.remove(user_to_remove)
    db.commit()

    return {"message": f"User {username} removed from chat {chat.name}"}

@app.post("/messages/")
async def send_message(msg: MessageCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Сохраняем сообщение в базу данных
    message = create_message(db, msg, current_user.id)

    # Создаем payload для отправки через WebSocket
    import json
    payload = {
        "id": message.id,
        "content": msg.content,  # Отправляем нешифрованное сообщение
        "timestamp": message.timestamp.isoformat(),
        "user": {
            "id": current_user.id,
            "username": current_user.username
        }
    }
    
    # Рассылаем сообщение всем в чате
    print(f"Attempting to broadcast to chat {msg.chat_id}", flush=True)
    await manager.broadcast_to_chat(json.dumps(payload), str(msg.chat_id))
    
    return message

@app.get("/chats/{chat_id}/messages")
def get_chat_messages(chat_id: int, skip: int = 0, limit: int = 60, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получить сообщения чата"""
    # Проверяем, что чат существует
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Проверяем, что пользователь является участником чата
    if current_user not in chat.members:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    messages = get_messages(db, chat_id, skip=skip, limit=limit)
    return messages

@app.get("/messages/{chat_id}")
def read_messages(chat_id: int, skip: int = 0, limit: int = 60, db: Session = Depends(get_db)):
    messages = get_messages(db, chat_id, skip=skip, limit=limit)
    return messages

@app.get("/online-users/")
def online_users():
    return get_online_users()

@app.websocket("/ws")
async def websocket_general_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """Общий WebSocket endpoint для подключения пользователя"""
    try:
        current_user = await get_current_user_ws(token=token, db=db)
        await websocket.accept()

        # Добавляем пользователя в онлайн
        from redis_client import add_online_user
        add_online_user(current_user.id, current_user.username)

        # Словарь для отслеживания чатов, к которым подключен пользователь
        user_chats = set()

        # Держим соединение открытым и обрабатываем сообщения
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Обрабатываем сообщение в зависимости от типа
                if message_data.get("type") == "chat_message":
                    chat_id = str(message_data.get("chat_id"))
                    content = message_data.get("content")

                    # Проверяем, что пользователь является участником чата
                    chat = db.query(models.Chat).filter(models.Chat.id == int(chat_id)).first()
                    if not chat or current_user not in chat.members:
                        continue

                    # Создаем объект MessageCreate для сохранения
                    msg = MessageCreate(chat_id=int(chat_id), content=content)

                    # Сохраняем сообщение в БД
                    db_message = create_message(db=db, message=msg, user_id=current_user.id)

                    # Отправляем сообщение всем участникам чата
                    broadcast_data = {
                        "type": "chat_message",
                        "chat_id": int(chat_id),
                        "id": db_message.id,
                        "username": current_user.username,
                        "content": content,
                        "timestamp": db_message.timestamp.isoformat()
                    }
                    await manager.broadcast_to_chat(json.dumps(broadcast_data), chat_id)

                elif message_data.get("type") == "join_chat":
                    # Подключаем пользователя к чату
                    chat_id = str(message_data.get("chat_id"))

                    # Проверяем, что пользователь является участником чата
                    chat = db.query(models.Chat).filter(models.Chat.id == int(chat_id)).first()
                    if chat and current_user in chat.members:
                        # Добавляем соединение к менеджеру для этого чата
                        if chat_id not in manager.active_connections:
                            manager.active_connections[chat_id] = []
                        if websocket not in manager.active_connections[chat_id]:
                            manager.active_connections[chat_id].append(websocket)
                            user_chats.add(chat_id)
                            print(f"User {current_user.username} joined chat {chat_id}", flush=True)

                elif message_data.get("type") == "leave_chat":
                    # Отключаем пользователя от чата
                    chat_id = str(message_data.get("chat_id"))
                    if chat_id in user_chats:
                        if chat_id in manager.active_connections and websocket in manager.active_connections[chat_id]:
                            manager.active_connections[chat_id].remove(websocket)
                            user_chats.remove(chat_id)
                            print(f"User {current_user.username} left chat {chat_id}", flush=True)

        except WebSocketDisconnect:
            pass
        finally:
            # Удаляем пользователя из всех чатов
            for chat_id in user_chats:
                if chat_id in manager.active_connections and websocket in manager.active_connections[chat_id]:
                    manager.active_connections[chat_id].remove(websocket)

            from redis_client import remove_online_user
            remove_online_user(current_user.id)

    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str, token: str, db: Session = Depends(get_db)):
    try:
        current_user = await get_current_user_ws(token=token, db=db)
        await handle_websocket(websocket, chat_id, current_user.id)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)