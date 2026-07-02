from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.database.health import check_database_connection, check_redis_connection
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def health_check() -> HealthResponse | JSONResponse:
    database_connected = await check_database_connection()
    redis_connected = await check_redis_connection()

    response = HealthResponse(
        status="ok" if database_connected and redis_connected else "degraded",
        database="connected" if database_connected else "disconnected",
        redis="connected" if redis_connected else "disconnected",
    )

    if response.status != "ok":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=response.model_dump()
        )

    return response
