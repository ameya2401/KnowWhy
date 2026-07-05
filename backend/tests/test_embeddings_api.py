from datetime import UTC, datetime
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.database.session import get_database_session
from app.main import create_app
from app.models.user import AuthProvider, User
from app.services.embedding_queue import EmbeddingQueueService, ProjectQueueState
import app.api.routes.embeddings as embeddings_router
from app.services.embeddings import EmbeddingService


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = create_app()

    # Override get_database_session to bypass DB operations
    async def override_db():
        yield None

    # Override get_current_user
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

    app.dependency_overrides[get_database_session] = override_db
    app.dependency_overrides[get_current_user] = override_current_user

    # Bypass project membership check in the router
    async def mock_require_membership(*args, **kwargs):
        return None

    monkeypatch.setattr(embeddings_router, "require_project_membership", mock_require_membership)

    return TestClient(app)


def test_get_indexing_status(client: TestClient) -> None:
    proj_id = str(uuid4())
    response = client.get(f"/embeddings/status?project_id={proj_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == proj_id
    assert data["status"] in ["idle", "paused", "running", "completed", "failed"]


def test_start_indexing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    proj_id = str(uuid4())

    async def mock_start(project_id):
        state = ProjectQueueState(project_id)
        state.status = "running"
        state.total_items = 10
        state.processed_items = 0
        state.failed_items = 0
        state.last_index_time = None
        state.error_message = None
        return state

    monkeypatch.setattr(EmbeddingQueueService, "start_indexing", mock_start)

    response = client.post("/embeddings/index", json={"project_id": proj_id})
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == proj_id
    assert data["status"] == "running"


def test_pause_indexing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    proj_id = str(uuid4())

    async def mock_pause(project_id):
        state = ProjectQueueState(project_id)
        state.status = "paused"
        state.total_items = 10
        state.processed_items = 4
        state.failed_items = 0
        state.last_index_time = None
        state.error_message = None
        return state

    monkeypatch.setattr(EmbeddingQueueService, "pause_indexing", mock_pause)

    response = client.post("/embeddings/pause", json={"project_id": proj_id})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paused"


def test_resume_indexing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    proj_id = str(uuid4())

    async def mock_resume(project_id):
        state = ProjectQueueState(project_id)
        state.status = "running"
        state.total_items = 10
        state.processed_items = 4
        state.failed_items = 0
        state.last_index_time = None
        state.error_message = None
        return state

    monkeypatch.setattr(EmbeddingQueueService, "resume_indexing", mock_resume)

    response = client.post("/embeddings/resume", json={"project_id": proj_id})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"


def test_reindex_project(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    proj_id = str(uuid4())

    async def mock_reindex(project_id):
        state = ProjectQueueState(project_id)
        state.status = "running"
        state.total_items = 10
        state.processed_items = 0
        state.failed_items = 0
        state.last_index_time = None
        state.error_message = None
        return state

    monkeypatch.setattr(EmbeddingQueueService, "reindex_project", mock_reindex)

    response = client.post("/embeddings/reindex", json={"project_id": proj_id})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"


def test_embedding_statistics(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    proj_id = str(uuid4())

    async def mock_get_statistics(self, project_id):
        return {
            "total_chunks": 42,
            "indexed_documents": 5,
        }

    monkeypatch.setattr(EmbeddingService, "get_statistics", mock_get_statistics)

    response = client.get(f"/embeddings/statistics?project_id={proj_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_vectors"] == 42
    assert data["indexed_documents"] == 5
    assert "queue_size" in data
    assert "failed_jobs" in data
