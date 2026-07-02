import logging

from app.database.health import check_database_connection, check_redis_connection

logger = logging.getLogger(__name__)


async def validate_external_services() -> None:
    database_connected = await check_database_connection()
    redis_connected = await check_redis_connection()

    if not database_connected or not redis_connected:
        unavailable = []
        if not database_connected:
            unavailable.append("database")
        if not redis_connected:
            unavailable.append("redis")
        raise RuntimeError(f"External service validation failed: {', '.join(unavailable)}")

    logger.info("External service validation succeeded.")
