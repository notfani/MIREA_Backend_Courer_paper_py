import redis
import json
import os

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))

def add_online_user(user_id: int, username: str):
    redis_client.sadd("online_users", user_id)
    redis_client.set(f"user:{user_id}", username)

def remove_online_user(user_id: int):
    redis_client.srem("online_users", user_id)
    redis_client.delete(f"user:{user_id}")

def get_online_users():
    user_ids = redis_client.smembers("online_users")
    users = []
    for uid in user_ids:
        username = redis_client.get(f"user:{uid}")
        users.append({"id": int(uid), "username": username})
    return users

def cache_message(chat_id: str, message_data: dict):
    redis_client.lpush(f"chat:{chat_id}", json.dumps(message_data))
    redis_client.ltrim(f"chat:{chat_id}", 0, 99)

def get_cached_messages(chat_id: str):
    messages = redis_client.lrange(f"chat:{chat_id}", 0, -1)
    return [json.loads(msg) for msg in messages]

def publish_notification(user_id: int, notification: str):
    redis_client.publish(f"notifications:{user_id}", notification)