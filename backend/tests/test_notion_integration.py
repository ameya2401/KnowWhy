from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.integrations.normalizer import NotionNormalizer
from app.integrations.security import encrypt_credentials
from app.integrations.service import IntegrationService
from app.models.integration import (
    Integration,
    IntegrationProvider,
    IntegrationStatus,
    NotionPage,
)
from app.models.organization import OrganizationMembership, OrganizationRole
from app.models.project import Project, ProjectMember, ProjectRole
from app.models.user import AuthProvider, User


def make_user(email: str = "user@example.com", name: str = "Test User") -> User:
    return User(
        id=uuid4(),
        email=email,
        full_name=name,
        profile_picture_url=None,
        provider=AuthProvider.GITHUB,
        provider_id=str(uuid4()),
        is_active=True,
        last_login_at=datetime.now(UTC),
    )


class FakeIntegrations:
    def __init__(self) -> None:
        self.by_id: dict[object, Integration] = {}
        self.by_project_provider: dict[tuple, Integration] = {}

    async def create(self, integration: Integration) -> Integration:
        integration.id = uuid4()
        self.by_id[integration.id] = integration
        self.by_project_provider[(integration.project_id, integration.provider)] = integration
        return integration

    async def get_by_id(self, integration_id) -> Integration | None:
        return self.by_id.get(integration_id)

    async def get_by_project_and_provider(self, project_id, provider) -> Integration | None:
        return self.by_project_provider.get((project_id, provider))

    async def delete(self, integration: Integration) -> None:
        if integration.id in self.by_id:
            del self.by_id[integration.id]
        if (integration.project_id, integration.provider) in self.by_project_provider:
            del self.by_project_provider[(integration.project_id, integration.provider)]


class FakeSyncData:
    def __init__(self) -> None:
        self.notion_pages = []

    async def create_notion_page(self, page: NotionPage) -> NotionPage:
        page.id = uuid4()
        self.notion_pages.append(page)
        return page

    async def get_notion_page_by_notion_id(
        self, integration_id, notion_page_id
    ) -> NotionPage | None:
        for p in self.notion_pages:
            if p.integration_id == integration_id and p.notion_page_id == notion_page_id:
                return p
        return None

    async def list_notion_pages_for_integration(self, integration_id) -> list[NotionPage]:
        return [p for p in self.notion_pages if p.integration_id == integration_id]


class FakeProjects:
    def __init__(self) -> None:
        self.projects: dict[object, Project] = {}

    def add(self, project: Project) -> None:
        self.projects[project.id] = project

    async def get_by_id(self, project_id) -> Project | None:
        return self.projects.get(project_id)


class FakeProjectMembers:
    def __init__(self) -> None:
        self.members: dict[tuple, ProjectMember] = {}

    def add(self, member: ProjectMember) -> None:
        self.members[(member.project_id, member.user_id)] = member

    async def get(self, project_id, user_id) -> ProjectMember | None:
        return self.members.get((project_id, user_id))


class FakeOrgMemberships:
    def __init__(self) -> None:
        self.memberships: dict[tuple, OrganizationMembership] = {}

    def add(self, membership: OrganizationMembership) -> None:
        self.memberships[(membership.organization_id, membership.user_id)] = membership

    async def get(self, organization_id, user_id) -> OrganizationMembership | None:
        return self.memberships.get((organization_id, user_id))


class FakeSession:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True

    async def flush(self) -> None:
        pass


def build_service() -> tuple[
    IntegrationService,
    FakeSession,
    FakeIntegrations,
    FakeSyncData,
    FakeProjects,
    FakeProjectMembers,
    FakeOrgMemberships,
]:
    session = FakeSession()
    service = IntegrationService(session)  # type: ignore[arg-type]

    fake_integrations = FakeIntegrations()
    fake_sync = FakeSyncData()
    fake_projects = FakeProjects()
    fake_members = FakeProjectMembers()
    fake_org_members = FakeOrgMemberships()

    service.integrations = fake_integrations  # type: ignore[assignment]
    service.sync_data = fake_sync  # type: ignore[assignment]
    service.projects = fake_projects  # type: ignore[assignment]
    service.project_members = fake_members  # type: ignore[assignment]
    service.org_service.memberships = fake_org_members  # type: ignore[assignment]

    return (
        service,
        session,
        fake_integrations,
        fake_sync,
        fake_projects,
        fake_members,
        fake_org_members,
    )


@pytest.mark.asyncio
async def test_connect_notion_requires_permissions() -> None:
    service, _, _, _, _, _, _ = build_service()
    user = make_user()
    project_id = uuid4()

    # No project membership -> Forbidden
    with pytest.raises(HTTPException) as exc:
        await service.connect_notion(user, project_id, "mock-code")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_connect_notion_requires_maintainer_role() -> None:
    service, _, _, _, fake_projects, fake_members, _ = build_service()
    user = make_user()
    project_id = uuid4()
    org_id = uuid4()

    proj = Project(
        id=project_id,
        organization_id=org_id,
        name="Test Project",
        slug="test",
        created_by_id=user.id,
    )
    fake_projects.add(proj)
    fake_members.add(ProjectMember(project_id=project_id, user_id=user.id, role=ProjectRole.VIEWER))

    # Viewer role is not enough
    with pytest.raises(HTTPException) as exc:
        await service.connect_notion(user, project_id, "mock-code")
    assert exc.value.status_code == 403
    assert "permissions" in exc.value.detail


@pytest.mark.asyncio
@patch("app.integrations.notion_client.NotionAPIClient.exchange_code_for_token")
async def test_connect_notion_success(mock_exchange: AsyncMock) -> None:
    (
        service,
        _,
        fake_integrations,
        _,
        fake_projects,
        fake_members,
        fake_org_members,
    ) = build_service()
    user = make_user()
    project_id = uuid4()
    org_id = uuid4()

    proj = Project(
        id=project_id,
        organization_id=org_id,
        name="Test Project",
        slug="test",
        created_by_id=user.id,
    )
    fake_projects.add(proj)
    fake_members.add(ProjectMember(project_id=project_id, user_id=user.id, role=ProjectRole.OWNER))
    fake_org_members.add(
        OrganizationMembership(
            organization_id=org_id, user_id=user.id, role=OrganizationRole.MEMBER
        )
    )

    mock_exchange.return_value = {
        "access_token": "secret-notion-token",
        "workspace_id": "workspace-123",
        "workspace_name": "My Notion Workspace",
        "workspace_icon": "https://example.com/icon.png",
    }

    integration = await service.connect_notion(user, project_id, "mock-code")

    assert integration.provider == IntegrationProvider.NOTION
    assert integration.status == IntegrationStatus.CONNECTED
    assert integration.workspace_id == "workspace-123"
    assert integration.workspace_name == "My Notion Workspace"
    assert integration.workspace_icon == "https://example.com/icon.png"
    assert integration.connected_by_id == user.id


def test_notion_normalizer_page() -> None:
    normalizer = NotionNormalizer()
    integration_id = uuid4()

    raw_page = {
        "object": "page",
        "id": "page-123",
        "parent": {
            "type": "page_id",
            "page_id": "parent-456",
        },
        "properties": {
            "title": {
                "id": "title",
                "type": "title",
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "My Page Title"},
                        "plain_text": "My Page Title",
                    }
                ],
            }
        },
        "url": "https://notion.so/page-123",
        "created_time": "2026-07-03T10:00:00.000Z",
        "last_edited_time": "2026-07-03T12:00:00.000Z",
        "last_edited_by": {
            "object": "user",
            "id": "author-99",
            "name": "Jane Doe",
        },
        "archived": False,
    }

    page = normalizer.normalize_page(integration_id, raw_page)
    assert page.integration_id == integration_id
    assert page.notion_page_id == "page-123"
    assert page.parent_id == "parent-456"
    assert page.title == "My Page Title"
    assert page.url == "https://notion.so/page-123"
    assert page.author == "Jane Doe"
    assert not page.archived


def test_notion_normalizer_database() -> None:
    normalizer = NotionNormalizer()
    integration_id = uuid4()

    raw_db = {
        "object": "database",
        "id": "db-789",
        "parent": {
            "type": "workspace",
            "workspace": True,
        },
        "title": [
            {
                "type": "text",
                "text": {"content": "My Database Title"},
                "plain_text": "My Database Title",
            }
        ],
        "url": "https://notion.so/db-789",
        "created_time": "2026-07-03T10:00:00.000Z",
        "last_edited_time": "2026-07-03T12:00:00.000Z",
        "last_edited_by": {
            "object": "user",
            "id": "author-99",
            "name": "Jane Doe",
        },
        "archived": False,
    }

    page = normalizer.normalize_page(integration_id, raw_db)
    assert page.notion_page_id == "db-789"
    assert page.parent_id is None
    assert page.title == "My Database Title"
    assert page.url == "https://notion.so/db-789"


@pytest.mark.asyncio
@patch("app.integrations.notion_client.NotionAPIClient.search")
async def test_sync_notion_incremental(mock_search: AsyncMock) -> None:
    service, _, fake_integrations, fake_sync, fake_projects, fake_members, _ = build_service()
    user = make_user()
    project_id = uuid4()
    org_id = uuid4()

    proj = Project(
        id=project_id,
        organization_id=org_id,
        name="Test Project",
        slug="test",
        created_by_id=user.id,
    )
    fake_projects.add(proj)
    fake_members.add(ProjectMember(project_id=project_id, user_id=user.id, role=ProjectRole.OWNER))

    # Save connected integration
    integration = Integration(
        organization_id=org_id,
        project_id=project_id,
        provider=IntegrationProvider.NOTION,
        status=IntegrationStatus.CONNECTED,
        credentials=encrypt_credentials({"access_token": "token"}),
        connected_by_id=user.id,
    )
    await fake_integrations.create(integration)

    # First sync returns 1 page
    mock_search.return_value = [
        {
            "object": "page",
            "id": "page-1",
            "parent": {"type": "workspace"},
            "properties": {
                "title": {
                    "type": "title",
                    "title": [{"plain_text": "Original Title"}],
                }
            },
            "url": "https://notion.so/page-1",
            "created_time": "2026-07-03T10:00:00.000Z",
            "last_edited_time": "2026-07-03T12:00:00.000Z",
            "last_edited_by": {"object": "user", "id": "user-1", "name": "Jane"},
            "archived": False,
        }
    ]

    await service.sync_notion(user, project_id)
    pages = await fake_sync.list_notion_pages_for_integration(integration.id)
    assert len(pages) == 1
    assert pages[0].title == "Original Title"

    # Second sync: page has been updated with newer timestamp
    mock_search.return_value = [
        {
            "object": "page",
            "id": "page-1",
            "parent": {"type": "workspace"},
            "properties": {
                "title": {
                    "type": "title",
                    "title": [{"plain_text": "Updated Title"}],
                }
            },
            "url": "https://notion.so/page-1",
            "created_time": "2026-07-03T10:00:00.000Z",
            "last_edited_time": "2026-07-03T13:00:00.000Z",  # newer
            "last_edited_by": {"object": "user", "id": "user-1", "name": "Jane"},
            "archived": False,
        }
    ]

    await service.sync_notion(user, project_id)
    pages = await fake_sync.list_notion_pages_for_integration(integration.id)
    assert len(pages) == 1
    assert pages[0].title == "Updated Title"

    # Third sync: page mock has older/same timestamp, should not overwrite
    mock_search.return_value = [
        {
            "object": "page",
            "id": "page-1",
            "parent": {"type": "workspace"},
            "properties": {
                "title": {
                    "type": "title",
                    "title": [{"plain_text": "Stale Title"}],
                }
            },
            "url": "https://notion.so/page-1",
            "created_time": "2026-07-03T10:00:00.000Z",
            "last_edited_time": "2026-07-03T12:00:00.000Z",  # older
            "last_edited_by": {"object": "user", "id": "user-1", "name": "Jane"},
            "archived": False,
        }
    ]

    await service.sync_notion(user, project_id)
    pages = await fake_sync.list_notion_pages_for_integration(integration.id)
    assert pages[0].title == "Updated Title"


@pytest.mark.asyncio
async def test_disconnect_notion_success() -> None:
    service, _, fake_integrations, _, fake_projects, fake_members, _ = build_service()
    user = make_user()
    project_id = uuid4()
    org_id = uuid4()

    proj = Project(
        id=project_id,
        organization_id=org_id,
        name="Test Project",
        slug="test",
        created_by_id=user.id,
    )
    fake_projects.add(proj)
    fake_members.add(ProjectMember(project_id=project_id, user_id=user.id, role=ProjectRole.OWNER))

    integration = Integration(
        organization_id=org_id,
        project_id=project_id,
        provider=IntegrationProvider.NOTION,
        status=IntegrationStatus.CONNECTED,
        connected_by_id=user.id,
    )
    await fake_integrations.create(integration)

    await service.disconnect_notion(user, project_id)
    assert await fake_integrations.get_by_project_and_provider(project_id, "notion") is None
