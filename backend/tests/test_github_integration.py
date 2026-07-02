from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.integrations.security import decrypt_credentials, encrypt_credentials
from app.integrations.service import IntegrationService
from app.models.integration import (
    Integration,
    IntegrationProvider,
    IntegrationRepository,
    IntegrationStatus,
)
from app.models.organization import OrganizationMembership
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


class FakeRepos:
    def __init__(self) -> None:
        self.by_id: dict[object, IntegrationRepository] = {}
        self.by_github_id: dict[tuple, IntegrationRepository] = {}

    async def create(self, repo: IntegrationRepository) -> IntegrationRepository:
        repo.id = uuid4()
        self.by_id[repo.id] = repo
        self.by_github_id[(repo.integration_id, repo.github_repo_id)] = repo
        return repo

    async def get_by_id(self, repo_id) -> IntegrationRepository | None:
        return self.by_id.get(repo_id)

    async def get_by_integration_and_github_id(
        self, integration_id, github_repo_id
    ) -> IntegrationRepository | None:
        return self.by_github_id.get((integration_id, github_repo_id))

    async def list_for_integration(self, integration_id) -> list[IntegrationRepository]:
        return [r for r in self.by_id.values() if r.integration_id == integration_id]

    async def delete(self, repo: IntegrationRepository) -> None:
        if repo.id in self.by_id:
            del self.by_id[repo.id]
        if (repo.integration_id, repo.github_repo_id) in self.by_github_id:
            del self.by_github_id[(repo.integration_id, repo.github_repo_id)]


class FakeSyncData:
    def __init__(self) -> None:
        self.commits = []
        self.prs = []
        self.issues = []

    async def create_commit(self, commit) -> None:
        commit.id = uuid4()
        self.commits.append(commit)

    async def get_commit_by_sha(self, repository_id, sha) -> None:
        for c in self.commits:
            if c.repository_id == repository_id and c.sha == sha:
                return c
        return None

    async def create_pull_request(self, pr) -> None:
        pr.id = uuid4()
        self.prs.append(pr)

    async def get_pull_request_by_github_id(self, repository_id, github_pr_id) -> None:
        for p in self.prs:
            if p.repository_id == repository_id and p.github_pr_id == github_pr_id:
                return p
        return None

    async def create_issue(self, issue) -> None:
        issue.id = uuid4()
        self.issues.append(issue)

    async def get_issue_by_github_id(self, repository_id, github_issue_id) -> None:
        for i in self.issues:
            if i.repository_id == repository_id and i.github_issue_id == github_issue_id:
                return i
        return None


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
    FakeRepos,
    FakeSyncData,
    FakeProjects,
    FakeProjectMembers,
    FakeOrgMemberships,
]:
    session = FakeSession()
    service = IntegrationService(session)  # type: ignore[arg-type]

    fake_integrations = FakeIntegrations()
    fake_repos = FakeRepos()
    fake_sync = FakeSyncData()
    fake_projects = FakeProjects()
    fake_members = FakeProjectMembers()
    fake_org_members = FakeOrgMemberships()

    service.integrations = fake_integrations  # type: ignore[assignment]
    service.repos = fake_repos  # type: ignore[assignment]
    service.sync_data = fake_sync  # type: ignore[assignment]
    service.projects = fake_projects  # type: ignore[assignment]
    service.project_members = fake_members  # type: ignore[assignment]
    service.org_service.memberships = fake_org_members  # type: ignore[assignment]

    return (
        service,
        session,
        fake_integrations,
        fake_repos,
        fake_sync,
        fake_projects,
        fake_members,
        fake_org_members,
    )


@pytest.mark.asyncio
async def test_connect_github_requires_permissions() -> None:
    service, _, _, _, _, _, _, _ = build_service()
    user = make_user()
    project_id = uuid4()

    # No project membership -> Forbidden
    with pytest.raises(HTTPException) as exc:
        await service.connect_github(user, project_id, "mock-code")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_connect_github_requires_maintainer_role() -> None:
    service, _, _, _, _, fake_projects, fake_members, _ = build_service()
    user = make_user()
    project_id = uuid4()
    org_id = uuid4()

    proj = Project(
        id=project_id,
        organization_id=org_id,
        name="Test",
        slug="test",
        created_by_id=user.id,
    )
    fake_projects.add(proj)
    fake_members.add(ProjectMember(project_id=project_id, user_id=user.id, role=ProjectRole.VIEWER))

    # Viewer role is not enough
    with pytest.raises(HTTPException) as exc:
        await service.connect_github(user, project_id, "mock-code")
    assert exc.value.status_code == 403
    assert "permissions" in exc.value.detail


@pytest.mark.asyncio
async def test_connect_repository_success() -> None:
    service, _, fake_integrations, fake_repos, _, fake_projects, fake_members, _ = build_service()
    user = make_user()
    project_id = uuid4()
    org_id = uuid4()

    proj = Project(
        id=project_id,
        organization_id=org_id,
        name="Test",
        slug="test",
        created_by_id=user.id,
    )
    fake_projects.add(proj)
    fake_members.add(ProjectMember(project_id=project_id, user_id=user.id, role=ProjectRole.OWNER))

    # Add connected integration first
    integration = Integration(
        organization_id=org_id,
        project_id=project_id,
        provider=IntegrationProvider.GITHUB,
        status=IntegrationStatus.CONNECTED,
        credentials=encrypt_credentials({"access_token": "token", "github_username": "username"}),
        connected_by_id=user.id,
    )
    await fake_integrations.create(integration)

    repo = await service.connect_repository(
        current_user=user,
        project_id=project_id,
        github_repo_id="12345",
        name="test-repo",
        owner="owner-name",
        default_branch="main",
        visibility="public",
        clone_url="https://github.com/owner-name/test-repo.git",
    )

    assert repo.name == "test-repo"
    assert repo.github_repo_id == "12345"
    assert repo.integration_id == integration.id


@pytest.mark.asyncio
async def test_disconnect_github_success() -> None:
    service, _, fake_integrations, _, _, fake_projects, fake_members, _ = build_service()
    user = make_user()
    project_id = uuid4()
    org_id = uuid4()

    proj = Project(
        id=project_id,
        organization_id=org_id,
        name="Test",
        slug="test",
        created_by_id=user.id,
    )
    fake_projects.add(proj)
    fake_members.add(ProjectMember(project_id=project_id, user_id=user.id, role=ProjectRole.OWNER))

    integration = Integration(
        organization_id=org_id,
        project_id=project_id,
        provider=IntegrationProvider.GITHUB,
        status=IntegrationStatus.CONNECTED,
        connected_by_id=user.id,
    )
    await fake_integrations.create(integration)

    # Disconnect
    await service.disconnect_github(user, project_id)
    assert await fake_integrations.get_by_project_and_provider(project_id, "github") is None


def test_encryption_decryption() -> None:
    creds = {"access_token": "secret-token", "user": "test-user"}
    encrypted = encrypt_credentials(creds)
    decrypted = decrypt_credentials(encrypted)
    assert decrypted == creds
