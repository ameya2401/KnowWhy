from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.models.organization import Organization
from app.models.user import User
from app.organizations.schemas import (
    ActiveOrganizationRead,
    ActiveOrganizationUpdate,
    InvitationCreate,
    InvitationRead,
    MembershipRoleUpdate,
    OrganizationCreate,
    OrganizationListItem,
    OrganizationMembershipRead,
    OrganizationRead,
    OrganizationUpdate,
)
from app.organizations.service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> Organization:
    return await OrganizationService(session).create_organization(current_user, payload)


@router.get("", response_model=list[OrganizationListItem])
async def list_organizations(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> list[OrganizationListItem]:
    memberships = await OrganizationService(session).list_organizations(current_user)
    return [
        OrganizationListItem(organization=membership.organization, role=membership.role)
        for membership in memberships
    ]


@router.get("/active", response_model=ActiveOrganizationRead)
async def get_active_organization(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ActiveOrganizationRead:
    if current_user.active_organization_id is None:
        return ActiveOrganizationRead(organization=None, role=None)
    service = OrganizationService(session)
    membership = await service.set_active_organization(
        current_user, current_user.active_organization_id
    )
    organization = await service.get_organization(current_user, membership.organization_id)
    return ActiveOrganizationRead(organization=organization, role=membership.role)


@router.put("/active", response_model=ActiveOrganizationRead)
async def set_active_organization(
    payload: ActiveOrganizationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ActiveOrganizationRead:
    service = OrganizationService(session)
    membership = await service.set_active_organization(current_user, payload.organization_id)
    organization = await service.get_organization(current_user, payload.organization_id)
    return ActiveOrganizationRead(organization=organization, role=membership.role)


@router.get("/{organization_id}", response_model=OrganizationRead)
async def get_organization(
    organization_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> Organization:
    return await OrganizationService(session).get_organization(current_user, organization_id)


@router.put("/{organization_id}", response_model=OrganizationRead)
async def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> Organization:
    return await OrganizationService(session).update_organization(
        current_user, organization_id, payload
    )


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> None:
    await OrganizationService(session).delete_organization(current_user, organization_id)


@router.post("/{organization_id}/invite", response_model=InvitationRead)
async def invite_member(
    organization_id: UUID,
    payload: InvitationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> InvitationRead:
    return await OrganizationService(session).invite_member(current_user, organization_id, payload)


@router.get("/{organization_id}/members", response_model=list[OrganizationMembershipRead])
async def list_members(
    organization_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> list[OrganizationMembershipRead]:
    return await OrganizationService(session).list_members(current_user, organization_id)


@router.put("/{organization_id}/members/{membership_id}", response_model=OrganizationMembershipRead)
async def update_member_role(
    organization_id: UUID,
    membership_id: UUID,
    payload: MembershipRoleUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> OrganizationMembershipRead:
    service = OrganizationService(session)
    membership = await service.update_member_role(
        current_user, organization_id, membership_id, payload
    )
    members = await service.list_members(current_user, organization_id)
    return next(member for member in members if member.id == membership.id)


@router.delete("/{organization_id}/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    organization_id: UUID,
    membership_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> None:
    await OrganizationService(session).remove_member(current_user, organization_id, membership_id)
