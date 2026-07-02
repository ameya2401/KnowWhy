import logging

from sqlalchemy import text

from app.database.session import engine

logger = logging.getLogger(__name__)


async def check_database_connection() -> bool:
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            return result.scalar_one() == 1
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", exc)
        return False


async def check_redis_connection() -> bool:
    from app.core.cache import create_redis_client

    client = create_redis_client()
    try:
        return bool(await client.ping())
    except Exception as exc:
        logger.warning("Redis connectivity check failed: %s", exc)
        return False
    finally:
        await client.aclose()
