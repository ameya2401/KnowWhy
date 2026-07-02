from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.organization import Organization, OrganizationMembership, OrganizationRole
from app.models.user import AuthProvider, User
from app.organizations.schemas import OrganizationCreate
from app.organizations.service import OrganizationService


def make_user(email: str = "owner@example.com") -> User:
    return User(
        id=uuid4(),
        email=email,
        full_name="Owner User",
        profile_picture_url=None,
        provider=AuthProvider.GITHUB,
        provider_id=str(uuid4()),
        is_active=True,
        last_login_at=datetime.now(UTC),
    )


class FakeOrganizations:
    def __init__(self) -> None:
        self.by_slug: dict[str, Organization] = {}
        self.by_id: dict[object, Organization] = {}
        self.deleted: Organization | None = None

    async def get_by_slug(self, slug: str) -> Organization | None:
        return self.by_slug.get(slug)

    async def create(self, organization: Organization) -> Organization:
        organization.id = uuid4()
        self.by_slug[organization.slug] = organization
        self.by_id[organization.id] = organization
        return organization

    async def get_by_id(self, organization_id):
        return self.by_id.get(organization_id)

    async def delete(self, organization: Organization) -> None:
        self.deleted = organization


class FakeMemberships:
    def __init__(self) -> None:
        self.memberships: list[OrganizationMembership] = []

    async def create(self, membership: OrganizationMembership) -> OrganizationMembership:
        membership.id = uuid4()
        self.memberships.append(membership)
        return membership

    async def get(self, organization_id, user_id):
        for membership in self.memberships:
            if membership.organization_id == organization_id and membership.user_id == user_id:
                return membership
        return None

    async def get_by_id(self, membership_id):
        for membership in self.memberships:
            if membership.id == membership_id:
                return membership
        return None


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


def build_service() -> tuple[OrganizationService, FakeSession, FakeOrganizations, FakeMemberships]:
    session = FakeSession()
    service = OrganizationService(session)  # type: ignore[arg-type]
    organizations = FakeOrganizations()
    memberships = FakeMemberships()
    service.organizations = organizations  # type: ignore[assignment]
    service.memberships = memberships  # type: ignore[assignment]
    return service, session, organizations, memberships


@pytest.mark.asyncio
async def test_create_organization_adds_owner_membership_and_active_workspace() -> None:
    service, session, _, memberships = build_service()
    user = make_user()

    organization = await service.create_organization(
        user,
        OrganizationCreate(name="KnowWhy Labs", slug="knowwhy-labs"),
    )

    assert organization.slug == "knowwhy-labs"
    assert user.active_organization_id == organization.id
    assert memberships.memberships[0].role == OrganizationRole.OWNER
    assert session.commits == 1


@pytest.mark.asyncio
async def test_member_cannot_delete_organization() -> None:
    service, _, organizations, memberships = build_service()
    user = make_user()
    organization = await organizations.create(
        Organization(name="KnowWhy Labs", slug="knowwhy-labs", created_by_id=user.id)
    )
    await memberships.create(
        OrganizationMembership(
            user_id=user.id,
            organization_id=organization.id,
            role=OrganizationRole.MEMBER,
        )
    )

    with pytest.raises(HTTPException) as exc:
        await service.delete_organization(user, organization.id)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_workspace_switch_requires_membership() -> None:
    service, _, _, _ = build_service()
    user = make_user()

    with pytest.raises(HTTPException) as exc:
        await service.set_active_organization(user, uuid4())

    assert exc.value.status_code == 404
