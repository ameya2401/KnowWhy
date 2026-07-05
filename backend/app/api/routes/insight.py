from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.models.project import Project, ProjectRole
from app.models.user import User
from app.projects.permissions import has_project_role_at_least
from app.repositories.projects import ProjectMemberRepository
from app.schemas.insight import (
    EngineeringInsightAnalyzeRequest,
    EngineeringInsightRead,
    EngineeringInsightStatistics,
)
from app.services.insight import InsightService

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


async def require_project_membership(
    current_user: User,
    project_id: UUID,
    db: AsyncSession,
    minimum_role: ProjectRole = ProjectRole.VIEWER,
) -> Project:
    """Enforces user membership inside the project and returns the Project object."""
    member_repo = ProjectMemberRepository(db)
    membership = await member_repo.get(project_id, current_user.id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Not a project member."
        )

    if not has_project_role_at_least(membership.role, minimum_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient project permissions."
        )

    # Fetch the project to get organization_id
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


@router.post("/analyze", response_model=list[EngineeringInsightRead])
async def analyze_project_insights(
    payload: EngineeringInsightAnalyzeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
    provider_override: str | None = None,
):
    """Triggers analysis for a project, generates, and persists engineering insights."""
    # Require at least CONTRIBUTOR/MAINTAINER to trigger analysis
    project = await require_project_membership(
        current_user, payload.project_id, db, ProjectRole.CONTRIBUTOR
    )  # noqa: E501

    insights = await InsightService.analyze_project_insights(
        db=db,
        project_id=project.id,
        organization_id=project.organization_id,
        provider_override=provider_override,
    )
    return insights


@router.get("/insights", response_model=list[EngineeringInsightRead])
async def list_insights(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
    status: str | None = None,
    severity: str | None = None,
    insight_type: str | None = None,
):
    """Lists engineering insights for a project."""
    project = await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)

    insights = await InsightService.list_project_insights(
        db=db,
        project_id=project.id,
        organization_id=project.organization_id,
        status=status,
        severity=severity,
        insight_type=insight_type,
    )
    return insights


@router.get("/insights/{id}", response_model=EngineeringInsightRead)
async def get_insight(
    id: UUID,
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Retrieves detailed information for a single engineering insight."""
    project = await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)

    insight = await InsightService.get_insight_by_id(
        db=db, insight_id=id, project_id=project.id, organization_id=project.organization_id
    )

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engineering insight not found."
        )
    return insight


@router.get("/statistics", response_model=EngineeringInsightStatistics)
async def get_statistics(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Returns statistics for a project's active insights."""
    project = await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)

    stats = await InsightService.get_insight_statistics(
        db=db, project_id=project.id, organization_id=project.organization_id
    )
    return stats
