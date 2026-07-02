from redis.asyncio import Redis

from app.core.config import settings
from app.database.health import check_redis_connection


def create_redis_client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def verify_redis_connection() -> bool:
    return await check_redis_connection()
