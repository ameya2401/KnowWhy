from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectMember


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.flush()
        return project

    async def get_by_id(self, project_id: UUID) -> Project | None:
        result = await self.session.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, organization_id: UUID, slug: str) -> Project | None:
        result = await self.session.execute(
            select(Project).where(
                Project.organization_id == organization_id,
                Project.slug == slug,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_organization(self, organization_id: UUID) -> list[Project]:
        result = await self.session.execute(
            select(Project)
            .where(Project.organization_id == organization_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)


class ProjectMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, membership: ProjectMember) -> ProjectMember:
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def get(self, project_id: UUID, user_id: UUID) -> ProjectMember | None:
        result = await self.session.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, membership_id: UUID) -> ProjectMember | None:
        result = await self.session.execute(
            select(ProjectMember).where(ProjectMember.id == membership_id)
        )
        return result.scalar_one_or_none()

    async def list_members(self, project_id: UUID) -> list[ProjectMember]:
        result = await self.session.execute(
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.joined_at.asc())
        )
        return list(result.scalars().all())

    async def delete(self, membership: ProjectMember) -> None:
        await self.session.delete(membership)
