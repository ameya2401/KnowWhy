from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.models.project import Project
from app.models.user import User
from app.projects.schemas import (
    ProjectCreate,
    ProjectMemberInvite,
    ProjectMemberRead,
    ProjectMemberRoleUpdate,
    ProjectRead,
    ProjectUpdate,
)
from app.projects.service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> Project:
    if current_user.active_organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active organization selected.",
        )
    return await ProjectService(session).create_project(
        current_user, current_user.active_organization_id, payload
    )


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> list[Project]:
    if current_user.active_organization_id is None:
        return []
    return await ProjectService(session).list_projects(
        current_user, current_user.active_organization_id
    )


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> Project:
    return await ProjectService(session).get_project(current_user, project_id)


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> Project:
    return await ProjectService(session).update_project(current_user, project_id, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> None:
    await ProjectService(session).delete_project(current_user, project_id)


@router.post("/{project_id}/archive", response_model=ProjectRead)
async def archive_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> Project:
    return await ProjectService(session).archive_project(current_user, project_id)


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberRead,
    status_code=status.HTTP_201_CREATED,
)
async def invite_member(
    project_id: UUID,
    payload: ProjectMemberInvite,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ProjectMemberRead:
    membership = await ProjectService(session).invite_member(current_user, project_id, payload)
    return ProjectMemberRead(
        id=membership.id,
        project_id=membership.project_id,
        user_id=membership.user_id,
        role=membership.role,
        joined_at=membership.joined_at,
        full_name=membership.user.full_name,
        email=membership.user.email,
        profile_picture_url=membership.user.profile_picture_url,
    )


@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
async def list_members(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> list[ProjectMemberRead]:
    memberships = await ProjectService(session).list_members(current_user, project_id)
    return [
        ProjectMemberRead(
            id=membership.id,
            project_id=membership.project_id,
            user_id=membership.user_id,
            role=membership.role,
            joined_at=membership.joined_at,
            full_name=membership.user.full_name,
            email=membership.user.email,
            profile_picture_url=membership.user.profile_picture_url,
        )
        for membership in memberships
    ]


@router.put("/{project_id}/members/{membership_id}", response_model=ProjectMemberRead)
async def update_member_role(
    project_id: UUID,
    membership_id: UUID,
    payload: ProjectMemberRoleUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ProjectMemberRead:
    service = ProjectService(session)
    membership = await service.update_member_role(
        current_user, project_id, membership_id, payload.role
    )
    # Refresh to load user relation
    memberships = await service.list_members(current_user, project_id)
    return next(m for m in memberships if m.id == membership.id)


@router.delete("/{project_id}/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    project_id: UUID,
    membership_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> None:
    await ProjectService(session).remove_member(current_user, project_id, membership_id)
