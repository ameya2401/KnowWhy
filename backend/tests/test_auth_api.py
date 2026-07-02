from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.main import create_app
from app.models.user import AuthProvider, User


def test_users_me_returns_current_user_from_dependency_override() -> None:
    app = create_app()
    user = User(
        id=uuid4(),
        email="engineer@example.com",
        full_name="KnowWhy Engineer",
        profile_picture_url=None,
        provider=AuthProvider.GITHUB,
        provider_id="123",
        is_active=True,
        last_login_at=datetime.now(UTC),
    )

    async def override_current_user() -> User:
        return user

    app.dependency_overrides[get_current_user] = override_current_user
    client = TestClient(app)

    response = client.get("/users/me")

    assert response.status_code == 200
    assert response.json()["email"] == "engineer@example.com"
    assert response.json()["provider"] == "github"
