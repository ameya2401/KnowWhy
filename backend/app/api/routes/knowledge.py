from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.models.project import ProjectRole
from app.models.user import User
from app.projects.permissions import has_project_role_at_least
from app.repositories.projects import ProjectMemberRepository
from app.schemas.knowledge import (
    KnowledgeItemDetail,
    KnowledgeItemListResponse,
    KnowledgeItemRead,
    KnowledgeRelationshipRead,
    KnowledgeSyncLogRead,
)
from app.services.knowledge import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class SyncRequest(BaseModel):
    project_id: UUID


async def require_project_membership(
    current_user: User,
    project_id: UUID,
    db: AsyncSession,
    minimum_role: ProjectRole = ProjectRole.VIEWER,
):
    """Enforces user membership inside the project."""
    repo = ProjectMemberRepository(db)
    membership = await repo.get(project_id, current_user.id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Not a project member."
        )

    if not has_project_role_at_least(membership.role, minimum_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient project permissions."
        )
    return membership


@router.get("", response_model=KnowledgeItemListResponse)
async def list_knowledge_items(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
    source: str | None = None,
    entity_type: str | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)
    service = KnowledgeService(db)
    items, total = await service.list_items(
        project_id=project_id,
        source=source,
        entity_type=entity_type,
        status=status,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total}


@router.get("/timeline", response_model=list[KnowledgeItemRead])
async def get_knowledge_timeline(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
    limit: int = 50,
    offset: int = 0,
):
    await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)
    service = KnowledgeService(db)
    return await service.get_timeline(project_id, limit, offset)


@router.get("/relationships/{id}", response_model=list[KnowledgeRelationshipRead])
async def list_item_relationships(
    id: UUID,
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)
    service = KnowledgeService(db)
    # Check if item exists first
    item = await service.get_item_by_id(id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Knowledge item not found.")
    return await service.list_relationships(id)


@router.get("/{id}", response_model=KnowledgeItemDetail)
async def get_knowledge_item_detail(
    id: UUID,
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)
    service = KnowledgeService(db)
    item = await service.get_item_by_id(id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Knowledge item not found.")
    return item


@router.post("/sync", response_model=KnowledgeSyncLogRead)
async def sync_knowledge(
    req: SyncRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    # Enforce minimum role contributor or contributor-equivalent.
    # Trigger normalization for all connected integrations.
    await require_project_membership(current_user, req.project_id, db, ProjectRole.CONTRIBUTOR)
    service = KnowledgeService(db)
    try:
        log = await service.sync_project_knowledge(req.project_id)
        return log
    except Exception as e:
        # Check if we have a failed sync log created in DB
        latest_log = await service.get_latest_sync_log(req.project_id)
        if latest_log and latest_log.status == "failed":
            return latest_log
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge synchronization failed: {str(e)}",
        ) from e
