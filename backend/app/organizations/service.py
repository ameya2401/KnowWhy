from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import (
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationRole,
)
from app.models.user import User
from app.organizations.permissions import has_role_at_least
from app.organizations.schemas import (
    InvitationCreate,
    MembershipRoleUpdate,
    OrganizationCreate,
    OrganizationMembershipRead,
    OrganizationUpdate,
)
from app.repositories.organizations import (
    InvitationRepository,
    MembershipRepository,
    OrganizationRepository,
)
from app.repositories.users import UserRepository


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.organizations = OrganizationRepository(session)
        self.memberships = MembershipRepository(session)
        self.invitations = InvitationRepository(session)
        self.users = UserRepository(session)

    async def create_organization(
        self, current_user: User, payload: OrganizationCreate
    ) -> Organization:
        existing = await self.organizations.get_by_slug(payload.slug)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Organization slug exists."
            )

        organization = await self.organizations.create(
            Organization(
                name=payload.name,
                slug=payload.slug,
                logo_url=payload.logo_url,
                description=payload.description,
                created_by_id=current_user.id,
            )
        )
        await self.memberships.create(
            OrganizationMembership(
                user_id=current_user.id,
                organization_id=organization.id,
                role=OrganizationRole.OWNER,
            )
        )
        current_user.active_organization_id = organization.id
        await self.session.commit()
        return organization

    async def list_organizations(self, current_user: User) -> list[OrganizationMembership]:
        return await self.organizations.list_for_user(current_user.id)

    async def get_organization(self, current_user: User, organization_id: UUID) -> Organization:
        await self.require_membership(current_user, organization_id, OrganizationRole.MEMBER)
        organization = await self.organizations.get_by_id(organization_id)
        if organization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found."
            )
        return organization

    async def update_organization(
        self,
        current_user: User,
        organization_id: UUID,
        payload: OrganizationUpdate,
    ) -> Organization:
        await self.require_membership(current_user, organization_id, OrganizationRole.ADMIN)
        organization = await self.get_organization(current_user, organization_id)
        if payload.name is not None:
            organization.name = payload.name
        if payload.logo_url is not None:
            organization.logo_url = payload.logo_url
        if payload.description is not None:
            organization.description = payload.description
        await self.session.commit()
        return organization

    async def delete_organization(self, current_user: User, organization_id: UUID) -> None:
        await self.require_membership(current_user, organization_id, OrganizationRole.OWNER)
        organization = await self.organizations.get_by_id(organization_id)
        if organization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found."
            )
        await self.organizations.delete(organization)
        if current_user.active_organization_id == organization_id:
            current_user.active_organization_id = None
        await self.session.commit()

    async def invite_member(
        self,
        current_user: User,
        organization_id: UUID,
        payload: InvitationCreate,
    ) -> OrganizationInvitation:
        await self.require_membership(current_user, organization_id, OrganizationRole.ADMIN)
        if payload.role == OrganizationRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot invite owners."
            )
        invitation = await self.invitations.create(
            OrganizationInvitation(
                organization_id=organization_id,
                email=payload.email.lower(),
                role=payload.role,
                invited_by_id=current_user.id,
            )
        )
        invited_user = await self.users.get_by_email(payload.email.lower())
        if (
            invited_user is not None
            and await self.memberships.get(organization_id, invited_user.id) is None
        ):
            await self.memberships.create(
                OrganizationMembership(
                    user_id=invited_user.id,
                    organization_id=organization_id,
                    role=payload.role,
                )
            )
        await self.session.commit()
        return invitation

    async def list_members(
        self,
        current_user: User,
        organization_id: UUID,
    ) -> list[OrganizationMembershipRead]:
        await self.require_membership(current_user, organization_id, OrganizationRole.MEMBER)
        memberships = await self.memberships.list_members(organization_id)
        return [
            OrganizationMembershipRead(
                id=membership.id,
                user_id=membership.user_id,
                organization_id=membership.organization_id,
                role=membership.role,
                joined_at=membership.joined_at,
                full_name=membership.user.full_name,
                email=membership.user.email,
                profile_picture_url=membership.user.profile_picture_url,
            )
            for membership in memberships
        ]

    async def update_member_role(
        self,
        current_user: User,
        organization_id: UUID,
        membership_id: UUID,
        payload: MembershipRoleUpdate,
    ) -> OrganizationMembership:
        await self.require_membership(current_user, organization_id, OrganizationRole.OWNER)
        target = await self.get_membership_in_org(organization_id, membership_id)
        if target.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change own role."
            )
        target.role = payload.role
        await self.session.commit()
        return target

    async def remove_member(
        self, current_user: User, organization_id: UUID, membership_id: UUID
    ) -> None:
        actor = await self.require_membership(current_user, organization_id, OrganizationRole.ADMIN)
        target = await self.get_membership_in_org(organization_id, membership_id)
        if target.role == OrganizationRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove owner."
            )
        if actor.role == OrganizationRole.ADMIN and target.role == OrganizationRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin cannot remove admin."
            )
        await self.memberships.delete(target)
        await self.session.commit()

    async def set_active_organization(
        self, current_user: User, organization_id: UUID
    ) -> OrganizationMembership:
        membership = await self.require_membership(
            current_user, organization_id, OrganizationRole.MEMBER
        )
        current_user.active_organization_id = organization_id
        await self.session.commit()
        return membership

    async def require_membership(
        self,
        current_user: User,
        organization_id: UUID,
        minimum_role: OrganizationRole,
    ) -> OrganizationMembership:
        membership = await self.memberships.get(organization_id, current_user.id)
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found."
            )
        if not has_role_at_least(membership.role, minimum_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role.")
        return membership

    async def get_membership_in_org(
        self,
        organization_id: UUID,
        membership_id: UUID,
    ) -> OrganizationMembership:
        membership = await self.memberships.get_by_id(membership_id)
        if membership is None or membership.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
        return membership
