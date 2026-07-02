from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.organization import Organization, OrganizationInvitation, OrganizationMembership


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, organization: Organization) -> Organization:
        self.session.add(organization)
        await self.session.flush()
        return organization

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        result = await self.session.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self.session.execute(select(Organization).where(Organization.slug == slug))
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: UUID) -> list[OrganizationMembership]:
        result = await self.session.execute(
            select(OrganizationMembership)
            .options(selectinload(OrganizationMembership.organization))
            .where(OrganizationMembership.user_id == user_id)
            .order_by(OrganizationMembership.joined_at.asc())
        )
        return list(result.scalars().all())

    async def delete(self, organization: Organization) -> None:
        await self.session.delete(organization)


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, membership: OrganizationMembership) -> OrganizationMembership:
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def get(self, organization_id: UUID, user_id: UUID) -> OrganizationMembership | None:
        result = await self.session.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, membership_id: UUID) -> OrganizationMembership | None:
        result = await self.session.execute(
            select(OrganizationMembership).where(OrganizationMembership.id == membership_id)
        )
        return result.scalar_one_or_none()

    async def list_members(self, organization_id: UUID) -> list[OrganizationMembership]:
        result = await self.session.execute(
            select(OrganizationMembership)
            .options(selectinload(OrganizationMembership.user))
            .where(OrganizationMembership.organization_id == organization_id)
            .order_by(OrganizationMembership.joined_at.asc())
        )
        return list(result.scalars().all())

    async def delete(self, membership: OrganizationMembership) -> None:
        await self.session.delete(membership)


class InvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, invitation: OrganizationInvitation) -> OrganizationInvitation:
        self.session.add(invitation)
        await self.session.flush()
        return invitation
