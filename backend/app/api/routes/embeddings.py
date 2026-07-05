from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.knowledge import require_project_membership
from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.models.project import ProjectRole
from app.models.user import User
from app.services.embedding_queue import EmbeddingQueueService
from app.services.embeddings import EmbeddingService

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


class EmbeddingProjectRequest(BaseModel):
    project_id: UUID


class EmbeddingQueueStatusResponse(BaseModel):
    project_id: UUID
    status: str
    total_items: int
    processed_items: int
    failed_items: int
    last_index_time: str | None
    error_message: str | None


class EmbeddingStatisticsResponse(BaseModel):
    total_vectors: int
    indexed_documents: int
    queue_size: int
    failed_jobs: int


@router.post("/index", response_model=EmbeddingQueueStatusResponse)
async def start_indexing(
    req: EmbeddingProjectRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    await require_project_membership(current_user, req.project_id, db, ProjectRole.CONTRIBUTOR)
    state = await EmbeddingQueueService.start_indexing(req.project_id)
    return {
        "project_id": state.project_id,
        "status": state.status,
        "total_items": state.total_items,
        "processed_items": state.processed_items,
        "failed_items": state.failed_items,
        "last_index_time": state.last_index_time,
        "error_message": state.error_message,
    }


@router.get("/status", response_model=EmbeddingQueueStatusResponse)
async def get_status(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)
    state = EmbeddingQueueService.get_state(project_id)
    return {
        "project_id": state.project_id,
        "status": state.status,
        "total_items": state.total_items,
        "processed_items": state.processed_items,
        "failed_items": state.failed_items,
        "last_index_time": state.last_index_time,
        "error_message": state.error_message,
    }


@router.post("/pause", response_model=EmbeddingQueueStatusResponse)
async def pause_indexing(
    req: EmbeddingProjectRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    await require_project_membership(current_user, req.project_id, db, ProjectRole.CONTRIBUTOR)
    state = await EmbeddingQueueService.pause_indexing(req.project_id)
    return {
        "project_id": state.project_id,
        "status": state.status,
        "total_items": state.total_items,
        "processed_items": state.processed_items,
        "failed_items": state.failed_items,
        "last_index_time": state.last_index_time,
        "error_message": state.error_message,
    }


@router.post("/resume", response_model=EmbeddingQueueStatusResponse)
async def resume_indexing(
    req: EmbeddingProjectRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    await require_project_membership(current_user, req.project_id, db, ProjectRole.CONTRIBUTOR)
    state = await EmbeddingQueueService.resume_indexing(req.project_id)
    return {
        "project_id": state.project_id,
        "status": state.status,
        "total_items": state.total_items,
        "processed_items": state.processed_items,
        "failed_items": state.failed_items,
        "last_index_time": state.last_index_time,
        "error_message": state.error_message,
    }


@router.post("/reindex", response_model=EmbeddingQueueStatusResponse)
async def reindex_project(
    req: EmbeddingProjectRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    await require_project_membership(current_user, req.project_id, db, ProjectRole.CONTRIBUTOR)
    state = await EmbeddingQueueService.reindex_project(req.project_id)
    return {
        "project_id": state.project_id,
        "status": state.status,
        "total_items": state.total_items,
        "processed_items": state.processed_items,
        "failed_items": state.failed_items,
        "last_index_time": state.last_index_time,
        "error_message": state.error_message,
    }


@router.get("/statistics", response_model=EmbeddingStatisticsResponse)
async def get_statistics(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    await require_project_membership(current_user, project_id, db, ProjectRole.VIEWER)
    embed_service = EmbeddingService(db)
    stats = await embed_service.get_statistics(project_id)
    queue_state = EmbeddingQueueService.get_state(project_id)

    queue_size = len(queue_state.pending_item_ids) if queue_state.status == "running" else 0

    return {
        "total_vectors": stats["total_chunks"],
        "indexed_documents": stats["indexed_documents"],
        "queue_size": queue_size,
        "failed_jobs": queue_state.failed_items,
    }
