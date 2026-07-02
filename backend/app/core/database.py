from app.database.health import check_database_connection
from app.database.session import async_session_factory

AsyncSessionLocal = async_session_factory


async def verify_database_connection() -> bool:
    return await check_database_connection()
