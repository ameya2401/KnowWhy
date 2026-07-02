import pytest
from fastapi.testclient import TestClient

import app.api.routes.health as health_route
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health_check_returns_ok_when_dependencies_are_connected(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def connected() -> bool:
        return True

    monkeypatch.setattr(health_route, "check_database_connection", connected)
    monkeypatch.setattr(health_route, "check_redis_connection", connected)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "connected",
        "redis": "connected",
    }


def test_health_check_reports_unavailable_dependencies(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def disconnected() -> bool:
        return False

    monkeypatch.setattr(health_route, "check_database_connection", disconnected)
    monkeypatch.setattr(health_route, "check_redis_connection", disconnected)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "database": "disconnected",
        "redis": "disconnected",
    }


def test_health_check_openapi_documents_connected_response() -> None:
    client = TestClient(create_app())

    schema = client.get("/openapi.json").json()

    health_schema = schema["components"]["schemas"]["HealthResponse"]["properties"]
    assert set(health_schema) == {"status", "database", "redis"}
