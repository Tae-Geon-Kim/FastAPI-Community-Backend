import redis.asyncio as redis
from app.core.config import redis_settings

redis_db = redis.Redis(
    host = redis_settings.REDIS_HOST,
    port = redis_settings.REDIS_PORT,
    password = redis_settings.REDIS_PASSWORD,
    decode_responses = True
)