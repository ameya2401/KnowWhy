import asyncio

from app.database.health import check_database_connection, check_redis_connection


async def main() -> None:
    database_ok = await check_database_connection()
    redis_ok = await check_redis_connection()

    if not database_ok:
        raise RuntimeError("PostgreSQL connection check failed.")
    if not redis_ok:
        raise RuntimeError("Redis connection check failed.")

    print("PostgreSQL and Redis connections verified.")


if __name__ == "__main__":
    asyncio.run(main())
