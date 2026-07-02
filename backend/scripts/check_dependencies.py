import asyncio

from app.core.cache import verify_redis_connection
from app.core.database import verify_database_connection


async def main() -> None:
    database_ok = await verify_database_connection()
    redis_ok = await verify_redis_connection()

    if not database_ok:
        raise RuntimeError("PostgreSQL connection check failed.")
    if not redis_ok:
        raise RuntimeError("Redis connection check failed.")

    print("PostgreSQL and Redis connections verified.")


if __name__ == "__main__":
    asyncio.run(main())
