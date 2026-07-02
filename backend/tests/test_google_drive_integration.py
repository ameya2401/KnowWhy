from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.integrations.security import encrypt_credentials
from app.integrations.service import IntegrationService
from app.models.integration import (
    DriveFile,
    Integration,
    IntegrationProvider,
    IntegrationStatus,
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
        self.drive_files = []

    async def create_drive_file(self, file: DriveFile) -> DriveFile:
        file.id = uuid4()
        self.drive_files.append(file)
        return file

    async def get_drive_file_by_google_id(self, integration_id, google_file_id) -> DriveFile | None:
        for f in self.drive_files:
            if f.integration_id == integration_id and f.google_file_id == google_file_id:
                return f
        return None

    async def list_drive_files_for_integration(self, integration_id) -> list[DriveFile]:
        return [f for f in self.drive_files if f.integration_id == integration_id]


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
async def test_connect_drive_requires_permissions() -> None:
    service, _, _, _, _, _, _ = build_service()
    user = make_user()
    project_id = uuid4()

    with pytest.raises(HTTPException) as exc:
        await service.connect_drive(user, project_id, "mock-code", "http://localhost/callback")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_connect_drive_requires_maintainer_role() -> None:
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

    with pytest.raises(HTTPException) as exc:
        await service.connect_drive(user, project_id, "mock-code", "http://localhost/callback")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
@patch("app.integrations.google_drive_client.GoogleDriveAPIClient.exchange_code_for_token")
async def test_connect_drive_success(mock_exchange: AsyncMock) -> None:
    (
        service,
        session,
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
    fake_members.add(
        ProjectMember(project_id=project_id, user_id=user.id, role=ProjectRole.MAINTAINER)
    )
    fake_org_members.add(
        OrganizationMembership(
            organization_id=org_id, user_id=user.id, role=OrganizationRole.MEMBER
        )
    )

    mock_exchange.return_value = {
        "access_token": "google-access-token",
        "refresh_token": "google-refresh-token",
        "email": "test@gmail.com",
    }

    integration = await service.connect_drive(
        user, project_id, "mock-code", "http://localhost/callback"
    )

    assert session.committed
    assert integration.provider == IntegrationProvider.GOOGLE_DRIVE
    assert integration.status == IntegrationStatus.CONNECTED
    assert integration.workspace_name == "test@gmail.com"
    assert integration.workspace_id == "test@gmail.com"

    saved = await fake_integrations.get_by_project_and_provider(project_id, "google_drive")
    assert saved is not None
    assert saved.id == integration.id


@pytest.mark.asyncio
@patch("app.integrations.google_drive_client.GoogleDriveAPIClient.get_file_content")
@patch("app.integrations.google_drive_client.GoogleDriveAPIClient.list_files")
async def test_sync_drive_success_and_incremental(
    mock_list_files: AsyncMock, mock_get_content: AsyncMock
) -> None:
    (
        service,
        _,
        fake_integrations,
        fake_sync,
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
    fake_members.add(ProjectMember(project_id=project_id, user_id=user.id, role=ProjectRole.VIEWER))
    fake_org_members.add(
        OrganizationMembership(
            organization_id=org_id, user_id=user.id, role=OrganizationRole.MEMBER
        )
    )

    credentials_data = {
        "access_token": "mock-token",
        "email": "test@gmail.com",
    }
    encrypted_creds = encrypt_credentials(credentials_data)

    integration = Integration(
        organization_id=org_id,
        project_id=project_id,
        provider=IntegrationProvider.GOOGLE_DRIVE,
        status=IntegrationStatus.CONNECTED,
        credentials=encrypted_creds,
        connected_by_id=user.id,
    )
    await fake_integrations.create(integration)

    # Initial sync setup
    mock_list_files.return_value = [
        {
            "id": "file-1",
            "name": "My Document",
            "mimeType": "application/vnd.google-apps.document",
            "parents": ["folder-1"],
            "size": "1024",
            "owners": [{"displayName": "Ameya"}],
            "webViewLink": "https://drive.google.com/file-1",
            "createdTime": "2026-07-03T10:00:00.000Z",
            "modifiedTime": "2026-07-03T12:00:00.000Z",
            "trashed": False,
        }
    ]
    mock_get_content.return_value = "Hello Google Drive World!"

    await service.sync_drive(user, project_id)

    files = await fake_sync.list_drive_files_for_integration(integration.id)
    assert len(files) == 1
    assert files[0].name == "My Document"
    assert files[0].content == "Hello Google Drive World!"

    # Second sync: modifiedTime updated, should fetch new content
    mock_list_files.return_value = [
        {
            "id": "file-1",
            "name": "My Document",
            "mimeType": "application/vnd.google-apps.document",
            "parents": ["folder-1"],
            "size": "2048",
            "owners": [{"displayName": "Ameya"}],
            "webViewLink": "https://drive.google.com/file-1",
            "createdTime": "2026-07-03T10:00:00.000Z",
            "modifiedTime": "2026-07-03T14:00:00.000Z",  # newer
            "trashed": False,
        }
    ]
    mock_get_content.return_value = "Updated content!"

    await service.sync_drive(user, project_id)
    files = await fake_sync.list_drive_files_for_integration(integration.id)
    assert len(files) == 1
    assert files[0].content == "Updated content!"


@pytest.mark.asyncio
async def test_disconnect_drive_success() -> None:
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
        provider=IntegrationProvider.GOOGLE_DRIVE,
        status=IntegrationStatus.CONNECTED,
        connected_by_id=user.id,
    )
    await fake_integrations.create(integration)

    await service.disconnect_drive(user, project_id)
    assert await fake_integrations.get_by_project_and_provider(project_id, "google_drive") is None
