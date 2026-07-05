from typing import Annotated
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.project import ProjectRole
from app.api.routes.knowledge import require_project_membership
from app.schemas.graph import (
    GraphResponse,
    EntityDetailResponse,
    TimelineResponse,
)
from app.schemas.knowledge import KnowledgeRelationshipRead
from app.services.graph import GraphService

router = APIRouter(tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
    limit: int = Query(default=500, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    entity_type: list[str] | None = Query(default=None),
):
    """
    Retrieves the Knowledge Graph (nodes and edges) for a project.
    Restricted to project members only.
    """
    await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)
    service = GraphService(db)
    return await service.get_project_graph(
        project_id=project_id,
        limit=limit,
        offset=offset,
        entity_types=entity_type,
    )


@router.get("/graph/entity/{id}", response_model=EntityDetailResponse)
async def get_entity_detail(
    id: str,
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """
    Retrieves detailed properties of a node and its direct neighbors.
    Restricted to project members only.
    """
    await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)
    service = GraphService(db)
    try:
        return await service.get_entity_detail(entity_id=id, project_id=project_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
    entity_type: str | None = None,
    source: str | None = None,
    author: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    Generates a chronological timeline of events for a project.
    Restricted to project members only.
    """
    await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)
    service = GraphService(db)
    return await service.get_project_timeline(
        project_id=project_id,
        entity_type=entity_type,
        source=source,
        author=author,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


@router.get("/timeline/project/{id}", response_model=TimelineResponse)
async def get_project_timeline_by_id(
    id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
    entity_type: str | None = None,
    source: str | None = None,
    author: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    Generates a chronological timeline of events for a project by project ID in the path.
    Restricted to project members only.
    """
    await require_project_membership(current_user, id, db, ProjectRole.VIEWER)
    service = GraphService(db)
    return await service.get_project_timeline(
        project_id=id,
        entity_type=entity_type,
        source=source,
        author=author,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


@router.get("/relationships/{id}", response_model=list[KnowledgeRelationshipRead])
async def get_relationships_by_node(
    id: UUID,
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """
    Retrieves all stored directional relationships for a given knowledge item UUID.
    Restricted to project members only.
    """
    await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)
    # Check if item exists and belongs to the project
    from app.services.knowledge import KnowledgeService
    k_service = KnowledgeService(db)
    item = await k_service.get_item_by_id(id)
    if not item or item.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge item not found.",
        )
    return await k_service.list_relationships(id)
