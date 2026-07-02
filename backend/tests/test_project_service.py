from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.organization import OrganizationMembership, OrganizationRole
from app.models.project import Project, ProjectMember, ProjectRole, ProjectVisibility
from app.models.user import AuthProvider, User
from app.projects.schemas import ProjectCreate, ProjectMemberInvite, ProjectUpdate
from app.projects.service import ProjectService


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


class FakeProjects:
    def __init__(self) -> None:
        self.by_id: dict[object, Project] = {}
        self.by_slug: dict[tuple, Project] = {}
        self.deleted: Project | None = None

    async def create(self, project: Project) -> Project:
        project.id = uuid4()
        self.by_id[project.id] = project
        self.by_slug[(project.organization_id, project.slug)] = project
        return project

    async def get_by_id(self, project_id) -> Project | None:
        return self.by_id.get(project_id)

    async def get_by_slug(self, organization_id, slug) -> Project | None:
        return self.by_slug.get((organization_id, slug))

    async def list_for_organization(self, organization_id) -> list[Project]:
        return [p for p in self.by_id.values() if p.organization_id == organization_id]

    async def delete(self, project: Project) -> None:
        self.deleted = project
        if project.id in self.by_id:
            del self.by_id[project.id]
        if (project.organization_id, project.slug) in self.by_slug:
            del self.by_slug[(project.organization_id, project.slug)]


class FakeProjectMembers:
    def __init__(self) -> None:
        self.memberships: list[ProjectMember] = []

    async def create(self, membership: ProjectMember) -> ProjectMember:
        membership.id = uuid4()
        self.memberships.append(membership)
        return membership

    async def get(self, project_id, user_id) -> ProjectMember | None:
        for m in self.memberships:
            if m.project_id == project_id and m.user_id == user_id:
                return m
        return None

    async def get_by_id(self, membership_id) -> ProjectMember | None:
        for m in self.memberships:
            if m.id == membership_id:
                return m
        return None

    async def list_members(self, project_id) -> list[ProjectMember]:
        return [m for m in self.memberships if m.project_id == project_id]

    async def delete(self, membership: ProjectMember) -> None:
        if membership in self.memberships:
            self.memberships.remove(membership)


class FakeOrgMemberships:
    def __init__(self) -> None:
        self.memberships: list[OrganizationMembership] = []

    async def get(self, organization_id, user_id) -> OrganizationMembership | None:
        for m in self.memberships:
            if m.organization_id == organization_id and m.user_id == user_id:
                return m
        return None

    async def create(self, membership: OrganizationMembership) -> OrganizationMembership:
        membership.id = uuid4()
        self.memberships.append(membership)
        return membership


class FakeUsers:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def add(self, user: User) -> None:
        self.users[user.email.lower()] = user

    async def get_by_email(self, email: str) -> User | None:
        return self.users.get(email.lower())


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


def build_service() -> tuple[
    ProjectService,
    FakeSession,
    FakeProjects,
    FakeProjectMembers,
    FakeOrgMemberships,
    FakeUsers,
]:
    session = FakeSession()
    service = ProjectService(session)  # type: ignore[arg-type]
    projects = FakeProjects()
    project_members = FakeProjectMembers()
    org_memberships = FakeOrgMemberships()
    users = FakeUsers()

    service.projects = projects  # type: ignore[assignment]
    service.project_members = project_members  # type: ignore[assignment]
    service.org_service.memberships = org_memberships  # type: ignore[assignment]
    service.users = users  # type: ignore[assignment]
    service.org_service.users = users  # type: ignore[assignment]

    return service, session, projects, project_members, org_memberships, users


@pytest.mark.asyncio
async def test_create_project_success() -> None:
    service, session, projects, project_members, org_memberships, _ = build_service()
    user = make_user()
    org_id = uuid4()

    # User must be org member first
    await org_memberships.create(
        OrganizationMembership(
            organization_id=org_id,
            user_id=user.id,
            role=OrganizationRole.MEMBER,
        )
    )

    payload = ProjectCreate(
        name="Project Alpha",
        slug="project-alpha",
        description="A great project",
        visibility=ProjectVisibility.PRIVATE,
    )

    project = await service.create_project(user, org_id, payload)

    assert project.name == "Project Alpha"
    assert project.slug == "project-alpha"
    assert project.organization_id == org_id
    assert project.created_by_id == user.id

    # Check project membership auto-created for owner
    assert len(project_members.memberships) == 1
    membership = project_members.memberships[0]
    assert membership.project_id == project.id
    assert membership.user_id == user.id
    assert membership.role == ProjectRole.OWNER
    assert session.commits == 1


@pytest.mark.asyncio
async def test_create_project_requires_org_membership() -> None:
    service, _, _, _, _, _ = build_service()
    user = make_user()
    org_id = uuid4()

    payload = ProjectCreate(
        name="Project Alpha",
        slug="project-alpha",
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_project(user, org_id, payload)

    assert exc.value.status_code == 404  # Organization not found / membership check failed


@pytest.mark.asyncio
async def test_cannot_create_duplicate_slug_in_same_org() -> None:
    service, _, _, _, org_memberships, _ = build_service()
    user = make_user()
    org_id = uuid4()

    await org_memberships.create(
        OrganizationMembership(
            organization_id=org_id,
            user_id=user.id,
            role=OrganizationRole.MEMBER,
        )
    )

    payload = ProjectCreate(name="Project Alpha", slug="project-alpha")
    await service.create_project(user, org_id, payload)

    # Attempt same slug
    with pytest.raises(HTTPException) as exc:
        await service.create_project(user, org_id, payload)

    assert exc.value.status_code == 409
    assert "slug exists" in exc.value.detail


@pytest.mark.asyncio
async def test_update_project_requires_maintainer() -> None:
    service, _, projects, project_members, org_memberships, _ = build_service()
    user = make_user()
    org_id = uuid4()

    await org_memberships.create(
        OrganizationMembership(
            organization_id=org_id,
            user_id=user.id,
            role=OrganizationRole.MEMBER,
        )
    )

    # Create project manually
    proj = await projects.create(
        Project(
            organization_id=org_id,
            name="Project Alpha",
            slug="project-alpha",
            visibility=ProjectVisibility.PRIVATE,
            created_by_id=uuid4(),
        )
    )

    # Join as Viewer
    await project_members.create(
        ProjectMember(project_id=proj.id, user_id=user.id, role=ProjectRole.VIEWER)
    )

    # Try updating
    with pytest.raises(HTTPException) as exc:
        await service.update_project(user, proj.id, ProjectUpdate(name="New Name"))

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_invite_member_success() -> None:
    service, _, projects, project_members, org_memberships, users = build_service()
    owner = make_user(email="owner@example.com")
    invitee = make_user(email="invitee@example.com")
    org_id = uuid4()

    users.add(owner)
    users.add(invitee)

    # Both belong to Organization
    await org_memberships.create(
        OrganizationMembership(
            organization_id=org_id,
            user_id=owner.id,
            role=OrganizationRole.MEMBER,
        )
    )
    await org_memberships.create(
        OrganizationMembership(
            organization_id=org_id,
            user_id=invitee.id,
            role=OrganizationRole.MEMBER,
        )
    )

    # Owner creates project
    proj = await projects.create(
        Project(
            organization_id=org_id,
            name="Project Alpha",
            slug="project-alpha",
            visibility=ProjectVisibility.PRIVATE,
            created_by_id=owner.id,
        )
    )
    await project_members.create(
        ProjectMember(project_id=proj.id, user_id=owner.id, role=ProjectRole.OWNER)
    )

    # Invite invitee
    payload = ProjectMemberInvite(email="invitee@example.com", role=ProjectRole.CONTRIBUTOR)
    membership = await service.invite_member(owner, proj.id, payload)

    assert membership.user_id == invitee.id
    assert membership.role == ProjectRole.CONTRIBUTOR
