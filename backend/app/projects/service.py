from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import OrganizationRole
from app.models.project import Project, ProjectMember, ProjectRole, ProjectStatus
from app.models.user import User
from app.organizations.service import OrganizationService
from app.projects.permissions import has_project_role_at_least
from app.projects.schemas import (
    ProjectCreate,
    ProjectMemberInvite,
    ProjectUpdate,
)
from app.repositories.projects import ProjectMemberRepository, ProjectRepository
from app.repositories.users import UserRepository


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.projects = ProjectRepository(session)
        self.project_members = ProjectMemberRepository(session)
        self.org_service = OrganizationService(session)
        self.users = UserRepository(session)

    async def create_project(
        self, current_user: User, organization_id: UUID, payload: ProjectCreate
    ) -> Project:
        # User must belong to organization to create projects
        await self.org_service.require_membership(
            current_user, organization_id, OrganizationRole.MEMBER
        )

        existing = await self.projects.get_by_slug(organization_id, payload.slug)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Project slug exists within this organization.",
            )

        project = await self.projects.create(
            Project(
                organization_id=organization_id,
                name=payload.name,
                slug=payload.slug,
                description=payload.description,
                visibility=payload.visibility,
                status=payload.status,
                color=payload.color,
                icon=payload.icon,
                created_by_id=current_user.id,
            )
        )

        # Creator is automatically Owner of the project
        await self.project_members.create(
            ProjectMember(
                project_id=project.id,
                user_id=current_user.id,
                role=ProjectRole.OWNER,
            )
        )

        await self.session.commit()
        return project

    async def list_projects(self, current_user: User, organization_id: UUID) -> list[Project]:
        # User must belong to organization
        await self.org_service.require_membership(
            current_user, organization_id, OrganizationRole.MEMBER
        )

        all_projects = await self.projects.list_for_organization(organization_id)

        # Filter: if user is not in the project and the project is private, they cannot see it.
        # Unless they are Org Admin or Org Owner? The PRD doesn't mention Org admins bypassing
        # project privacy, but standard RBAC usually isolates projects. Let's filter private
        # projects where user is not a member.
        accessible_projects = []
        for project in all_projects:
            if project.visibility == "public":
                accessible_projects.append(project)
            else:
                membership = await self.project_members.get(project.id, current_user.id)
                if membership is not None:
                    accessible_projects.append(project)

        return accessible_projects

    async def get_project(self, current_user: User, project_id: UUID) -> Project:
        project = await self.projects.get_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        # Check organization membership
        await self.org_service.require_membership(
            current_user, project.organization_id, OrganizationRole.MEMBER
        )

        # Check project membership if it is private
        if project.visibility == "private":
            await self.require_project_membership(current_user, project_id, ProjectRole.VIEWER)

        return project

    async def update_project(
        self, current_user: User, project_id: UUID, payload: ProjectUpdate
    ) -> Project:
        project = await self.get_project(current_user, project_id)

        # Only Owner or Maintainer can update project details
        # PRD says Owner: "Manage settings", Maintainer: "Update project"
        # Let's require Maintainer role for general updates, but Owner
        # for visibility/status/settings if needed.
        # Let's require MAINTAINER role at least
        await self.require_project_membership(current_user, project_id, ProjectRole.MAINTAINER)

        if payload.name is not None:
            project.name = payload.name
        if payload.description is not None:
            project.description = payload.description
        if payload.visibility is not None:
            # Visibility change requires OWNER
            await self.require_project_membership(current_user, project_id, ProjectRole.OWNER)
            project.visibility = payload.visibility
        if payload.status is not None:
            # Status change requires OWNER
            await self.require_project_membership(current_user, project_id, ProjectRole.OWNER)
            project.status = payload.status
        if payload.color is not None:
            project.color = payload.color
        if payload.icon is not None:
            project.icon = payload.icon

        await self.session.commit()
        return project

    async def delete_project(self, current_user: User, project_id: UUID) -> None:
        project = await self.get_project(current_user, project_id)

        # Only Owner can delete project
        await self.require_project_membership(current_user, project_id, ProjectRole.OWNER)

        await self.projects.delete(project)
        await self.session.commit()

    async def archive_project(self, current_user: User, project_id: UUID) -> Project:
        project = await self.get_project(current_user, project_id)

        # Only Owner can archive project
        await self.require_project_membership(current_user, project_id, ProjectRole.OWNER)

        project.status = ProjectStatus.ARCHIVED
        await self.session.commit()
        return project

    async def invite_member(
        self, current_user: User, project_id: UUID, payload: ProjectMemberInvite
    ) -> ProjectMember:
        project = await self.get_project(current_user, project_id)

        # Owner or Maintainer can invite members
        await self.require_project_membership(current_user, project_id, ProjectRole.MAINTAINER)

        target_user = await self.users.get_by_email(payload.email.lower())
        if target_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        # Target user must be a member of the organization
        await self.org_service.require_membership(
            target_user, project.organization_id, OrganizationRole.MEMBER
        )

        existing = await self.project_members.get(project_id, target_user.id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User is already a project member."
            )

        membership = await self.project_members.create(
            ProjectMember(
                project_id=project_id,
                user_id=target_user.id,
                role=payload.role,
            )
        )
        await self.session.commit()
        return membership

    async def list_members(self, current_user: User, project_id: UUID) -> list[ProjectMember]:
        await self.get_project(current_user, project_id)
        # Any authorized project viewer can list members
        await self.require_project_membership(current_user, project_id, ProjectRole.VIEWER)
        return await self.project_members.list_members(project_id)

    async def update_member_role(
        self, current_user: User, project_id: UUID, membership_id: UUID, new_role: ProjectRole
    ) -> ProjectMember:
        await self.get_project(current_user, project_id)

        # Only Owner can manage roles
        await self.require_project_membership(current_user, project_id, ProjectRole.OWNER)

        membership = await self.project_members.get_by_id(membership_id)
        if membership is None or membership.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found."
            )

        if membership.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change own project role."
            )

        membership.role = new_role
        await self.session.commit()
        return membership

    async def remove_member(
        self, current_user: User, project_id: UUID, membership_id: UUID
    ) -> None:
        await self.get_project(current_user, project_id)

        # Only Owner can remove members
        await self.require_project_membership(current_user, project_id, ProjectRole.OWNER)

        membership = await self.project_members.get_by_id(membership_id)
        if membership is None or membership.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found."
            )

        if membership.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove self from project."
            )

        await self.project_members.delete(membership)
        await self.session.commit()

    async def require_project_membership(
        self, current_user: User, project_id: UUID, minimum_role: ProjectRole
    ) -> ProjectMember:
        membership = await self.project_members.get(project_id, current_user.id)
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Not a project member."
            )

        if not has_project_role_at_least(membership.role, minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient project permissions."
            )

        return membership
