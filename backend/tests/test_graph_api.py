from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

import app.api.routes.graph as graph_router
from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.main import create_app
from app.models.user import AuthProvider, User
from app.schemas.graph import (
    EntityDetailResponse,
    EntityRelationshipDetail,
    GraphEdge,
    GraphNode,
    GraphResponse,
    NeighborInfo,
    TimelineEvent,
    TimelineResponse,
)
from app.schemas.knowledge import KnowledgeRelationshipRead
from app.services.graph import GraphService


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

    monkeypatch.setattr(graph_router, "require_project_membership", mock_require_membership)

    return TestClient(app)


def test_get_graph(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    project_id = str(uuid4())

    async def mock_get_project_graph(*args, **kwargs):
        return GraphResponse(
            nodes=[
                GraphNode(
                    id=f"project-{project_id}",
                    type="project",
                    title="Mock Project",
                    subtitle="mock-project",
                ),
                GraphNode(
                    id="user-1",
                    type="user",
                    title="Test Member",
                    subtitle="test@example.com",
                )
            ],
            edges=[
                GraphEdge(
                    id="edge-1",
                    source=f"project-{project_id}",
                    target="user-1",
                    type="contains",
                    confidence=1.0,
                )
            ]
        )

    monkeypatch.setattr(GraphService, "get_project_graph", mock_get_project_graph)

    response = client.get(f"/graph?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 2
    assert data["nodes"][0]["type"] == "project"
    assert data["nodes"][1]["type"] == "user"
    assert len(data["edges"]) == 1
    assert data["edges"][0]["type"] == "contains"


def test_get_entity_detail(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    project_id = str(uuid4())
    entity_id = "user-1"

    async def mock_get_entity_detail(*args, **kwargs):
        return EntityDetailResponse(
            entity=GraphNode(
                id=entity_id,
                type="user",
                title="Test Member",
                subtitle="test@example.com",
            ),
            relationships=[
                EntityRelationshipDetail(
                    neighbor=NeighborInfo(
                        id=f"project-{project_id}",
                        type="project",
                        title="Mock Project",
                    ),
                    edge_type="contains",
                    direction="incoming",
                    confidence=1.0,
                )
            ]
        )

    monkeypatch.setattr(GraphService, "get_entity_detail", mock_get_entity_detail)

    response = client.get(f"/graph/entity/{entity_id}?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["entity"]["id"] == entity_id
    assert len(data["relationships"]) == 1
    assert data["relationships"][0]["direction"] == "incoming"


def test_get_timeline(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    project_id = str(uuid4())

    async def mock_get_project_timeline(*args, **kwargs):
        return TimelineResponse(
            events=[
                TimelineEvent(
                    id="event-1",
                    type="commit",
                    title="Initial commit",
                    description="Init repo structure",
                    time=datetime.now(UTC),
                    author="Test Dev",
                )
            ]
        )

    monkeypatch.setattr(GraphService, "get_project_timeline", mock_get_project_timeline)

    response = client.get(f"/timeline?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 1
    assert data["events"][0]["type"] == "commit"
    assert data["events"][0]["author"] == "Test Dev"


def test_get_project_timeline_by_id(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    project_id = str(uuid4())

    async def mock_get_project_timeline(*args, **kwargs):
        return TimelineResponse(
            events=[
                TimelineEvent(
                    id="event-2",
                    type="pull_request",
                    title="Feature implementation",
                    description="Implement graph module",
                    time=datetime.now(UTC),
                    author="Test Dev",
                )
            ]
        )

    monkeypatch.setattr(GraphService, "get_project_timeline", mock_get_project_timeline)

    response = client.get(f"/timeline/project/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 1
    assert data["events"][0]["type"] == "pull_request"
    assert data["events"][0]["author"] == "Test Dev"


def test_get_relationships_by_node(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    project_id = str(uuid4())
    node_id = str(uuid4())

    # Mock get_item_by_id in KnowledgeService
    from app.services.knowledge import KnowledgeService
    class DummyItem:
        def __init__(self, nid, pid):
            self.id = nid
            self.project_id = pid

    async def mock_get_item_by_id(*args, **kwargs):
        return DummyItem(UUID(node_id), UUID(project_id))

    async def mock_list_relationships(*args, **kwargs):
        return [
            KnowledgeRelationshipRead(
                id=uuid4(),
                source_item_id=UUID(node_id),
                target_item_id=uuid4(),
                relationship_type="references",
                confidence=1.0,
                created_at=datetime.now(UTC),
            )
        ]

    monkeypatch.setattr(KnowledgeService, "get_item_by_id", mock_get_item_by_id)
    monkeypatch.setattr(KnowledgeService, "list_relationships", mock_list_relationships)

    response = client.get(f"/relationships/{node_id}?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["relationship_type"] == "references"
