from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

import app.api.routes.insight as insight_router
from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.main import create_app
from app.models.insight import EngineeringInsight
from app.models.knowledge import KnowledgeItem
from app.models.user import AuthProvider, User
from app.services.insight import InsightService
from app.services.insight_rules import (
    ArchitectureDriftRule,
    DocumentationGapRule,
    DuplicateKnowledgeRule,
    KnowledgeCoverageRule,
    ProjectHealthRule,
    StaleKnowledgeRule,
)


# Mock DB Execute Result
class MockExecuteResult:
    def __init__(self, scalar_values):
        self.scalar_values = scalar_values

    def scalars(self):
        return self


    def first(self):
        return self.scalar_values[0] if self.scalar_values else None

    def all(self):
        return self.scalar_values


@pytest.mark.asyncio
async def test_documentation_gap_rule():
    db = AsyncMock()
    project_id = uuid4()
    org_id = uuid4()

    # Case: Commit mentions "auth" but there's no notion docs mentioning "auth"
    commit = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        organization_id=org_id,
        source="github",
        source_entity_id="c1",
        entity_type="commit",
        title="Implement auth system module",
        description="Integrate security authentication",
        created_time=datetime.now(UTC),
        updated_time=datetime.now(UTC),
        status="active"
    )
    doc_page = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        organization_id=org_id,
        source="notion",
        source_entity_id="n1",
        entity_type="notion_page",
        title="Getting Started Guide",
        description="General guide",
        created_time=datetime.now(UTC),
        updated_time=datetime.now(UTC),
        status="active"
    )

    db.execute.side_effect = [
        MockExecuteResult([commit]),
        MockExecuteResult([doc_page])
    ]

    rule = DocumentationGapRule()
    insights = await rule.analyze(db, project_id, org_id)

    assert len(insights) >= 1
    assert insights[0]["rule_name"] == "documentation_gap"
    assert "auth" in insights[0]["title"].lower() or "security" in insights[0]["title"].lower()
    assert insights[0]["evidence_items"][0] == commit


@pytest.mark.asyncio
async def test_stale_knowledge_rule():
    db = AsyncMock()
    project_id = uuid4()
    org_id = uuid4()

    # Case: Document updated 40 days ago
    doc_page = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        organization_id=org_id,
        source="notion",
        source_entity_id="n1",
        entity_type="notion_page",
        title="Outdated Architecture spec",
        description="General guide",
        created_time=datetime.now(UTC) - timedelta(days=50),
        updated_time=datetime.now(UTC) - timedelta(days=40),
        status="active"
    )

    db.execute.return_value = MockExecuteResult([doc_page])

    rule = StaleKnowledgeRule()
    insights = await rule.analyze(db, project_id, org_id)

    assert len(insights) == 1
    assert insights[0]["rule_name"] == "stale_knowledge"
    assert "Outdated Architecture spec" in insights[0]["title"]


@pytest.mark.asyncio
async def test_architecture_drift_rule():
    db = AsyncMock()
    project_id = uuid4()
    org_id = uuid4()

    # Case: ADR specifies PostgreSQL, commit references MongoDB/MySQL
    adr = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        organization_id=org_id,
        source="notion",
        source_entity_id="adr1",
        entity_type="notion_page",
        title="ADR: PostgreSQL Database Decision",
        description="We decided to use postgresql.",
        content="postgresql details",
        created_time=datetime.now(UTC),
        updated_time=datetime.now(UTC),
        status="active"
    )
    commit = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        organization_id=org_id,
        source="github",
        source_entity_id="c2",
        entity_type="commit",
        title="Setup mongodb connector",
        description="Configure mysql",
        created_time=datetime.now(UTC),
        updated_time=datetime.now(UTC),
        status="active"
    )

    db.execute.side_effect = [
        MockExecuteResult([adr]),
        MockExecuteResult([commit])
    ]

    rule = ArchitectureDriftRule()
    insights = await rule.analyze(db, project_id, org_id)

    assert len(insights) == 1
    assert insights[0]["rule_name"] == "architecture_drift"
    assert "PostgreSQL" in insights[0]["title"]


@pytest.mark.asyncio
async def test_duplicate_knowledge_rule():
    db = AsyncMock()
    project_id = uuid4()
    org_id = uuid4()

    # Case: Two docs with identical titles
    doc1 = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        organization_id=org_id,
        source="notion",
        source_entity_id="d1",
        entity_type="notion_page",
        title="API Reference Guide",
        created_time=datetime.now(UTC),
        updated_time=datetime.now(UTC),
        status="active"
    )
    doc2 = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        organization_id=org_id,
        source="google_drive",
        source_entity_id="d2",
        entity_type="document",
        title="API Reference Guide",
        created_time=datetime.now(UTC),
        updated_time=datetime.now(UTC),
        status="active"
    )

    db.execute.return_value = MockExecuteResult([doc1, doc2])

    rule = DuplicateKnowledgeRule()
    insights = await rule.analyze(db, project_id, org_id)

    assert len(insights) == 1
    assert insights[0]["rule_name"] == "duplicate_knowledge"
    assert "API Reference Guide" in insights[0]["title"]


@pytest.mark.asyncio
async def test_project_health_rule():
    db = AsyncMock()
    project_id = uuid4()
    org_id = uuid4()

    # Case: High number of open issues (> 5)
    issues = [
        KnowledgeItem(
            id=uuid4(),
            project_id=project_id,
            organization_id=org_id,
            source="github",
            source_entity_id=f"issue_{i}",
            entity_type="issue",
            title=f"Bug #{i}",
            metadata_json={"state": "open"},
            created_time=datetime.now(UTC),
            updated_time=datetime.now(UTC),
            status="active"
        )
        for i in range(7)
    ]

    db.execute.return_value = MockExecuteResult(issues)

    rule = ProjectHealthRule()
    insights = await rule.analyze(db, project_id, org_id)

    assert len(insights) == 1
    assert insights[0]["rule_name"] == "project_health"
    assert "Issue Backlog" in insights[0]["title"]


@pytest.mark.asyncio
async def test_knowledge_coverage_rule():
    db = AsyncMock()
    project_id = uuid4()
    org_id = uuid4()

    # Case: Active codebase (> 10 commits) but zero doc pages
    commits = [
        KnowledgeItem(
            id=uuid4(),
            project_id=project_id,
            organization_id=org_id,
            source="github",
            source_entity_id=f"commit_{i}",
            entity_type="commit",
            title=f"Commit #{i}",
            created_time=datetime.now(UTC),
            updated_time=datetime.now(UTC),
            status="active"
        )
        for i in range(12)
    ]

    db.execute.side_effect = [
        MockExecuteResult(commits),
        MockExecuteResult([])
    ]

    rule = KnowledgeCoverageRule()
    insights = await rule.analyze(db, project_id, org_id)

    assert len(insights) == 1
    assert insights[0]["rule_name"] == "knowledge_coverage"
    assert "Zero Documentation" in insights[0]["title"]


@pytest.fixture
def test_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = create_app()

    async def override_db():
        yield None

    user = User(
        id=uuid4(),
        email="advisor@example.com",
        full_name="KnowWhy Advisor",
        profile_picture_url=None,
        provider=AuthProvider.GITHUB,
        provider_id="advisor-123",
        is_active=True,
        last_login_at=datetime.now(UTC),
    )

    async def override_current_user() -> User:
        return user

    app.dependency_overrides[get_database_session] = override_db
    app.dependency_overrides[get_current_user] = override_current_user

    async def mock_require_membership(*args, **kwargs):
        class MockProject:
            id = uuid4()
            organization_id = uuid4()
        return MockProject()

    monkeypatch.setattr(insight_router, "require_project_membership", mock_require_membership)

    return TestClient(app)


def test_api_analyze(test_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    project_id = str(uuid4())

    async def mock_analyze(*args, **kwargs):
        return [
            EngineeringInsight(
                id=uuid4(),
                project_id=UUID(project_id),
                organization_id=uuid4(),
                title="Mock AI Refined Insight",
                description="Refined with mock intelligence.",
                insight_type="documentation_gap",
                severity="warning",
                confidence=0.85,
                evidence=[],
                suggested_actions=["Verify details"],
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
        ]

    monkeypatch.setattr(InsightService, "analyze_project_insights", mock_analyze)

    resp = test_client.post("/intelligence/analyze", json={"project_id": project_id})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Mock AI Refined Insight"
    assert data[0]["severity"] == "warning"


def test_api_list_insights(test_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    project_id = str(uuid4())

    async def mock_list(*args, **kwargs):
        return [
            EngineeringInsight(
                id=uuid4(),
                project_id=UUID(project_id),
                organization_id=uuid4(),
                title="Active Insight",
                description="Needs action.",
                insight_type="project_health",
                severity="critical",
                confidence=0.95,
                evidence=[],
                suggested_actions=[],
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
        ]

    monkeypatch.setattr(InsightService, "list_project_insights", mock_list)

    resp = test_client.get(f"/intelligence/insights?project_id={project_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Active Insight"
    assert data[0]["severity"] == "critical"


def test_api_get_statistics(test_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    project_id = str(uuid4())

    async def mock_stats(*args, **kwargs):
        return {
            "total_insights": 1,
            "severity_breakdown": {"critical": 1, "warning": 0, "suggestion": 0},
            "type_breakdown": {
                "documentation_gap": 0,
                "stale_knowledge": 0,
                "architecture_drift": 0,
                "duplicate_knowledge": 0,
                "project_health": 1,
                "knowledge_coverage": 0
            },
            "average_confidence": 0.95
        }

    monkeypatch.setattr(InsightService, "get_insight_statistics", mock_stats)

    resp = test_client.get(f"/intelligence/statistics?project_id={project_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_insights"] == 1
    assert data["severity_breakdown"]["critical"] == 1
    assert data["average_confidence"] == 0.95
