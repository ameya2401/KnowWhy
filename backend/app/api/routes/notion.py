from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.integrations.service import IntegrationService
from app.models.project import ProjectRole
from app.models.user import User

router = APIRouter(prefix="/integrations/notion", tags=["integrations"])


class NotionConnectRequest(BaseModel):
    code: str
    project_id: UUID


class SyncRequest(BaseModel):
    project_id: UUID


@router.get("")
async def get_integration(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    await service.require_project_membership(current_user, project_id, ProjectRole.VIEWER)

    integration = await service.integrations.get_by_project_and_provider(project_id, "notion")
    if not integration:
        return {"connected": False, "integration": None, "pages": []}

    pages = await service.list_notion_pages(current_user, project_id)
    return {
        "connected": True,
        "integration": {
            "id": integration.id,
            "status": integration.status.value,
            "last_sync": integration.last_sync.isoformat() if integration.last_sync else None,
            "last_error": integration.last_error,
            "connected_at": integration.connected_at.isoformat(),
            "workspace_name": integration.workspace_name,
            "workspace_id": integration.workspace_id,
            "workspace_icon": integration.workspace_icon,
        },
        "pages": [
            {
                "id": str(p.id),
                "notion_page_id": p.notion_page_id,
                "parent_id": p.parent_id,
                "title": p.title,
                "url": p.url,
                "last_edited": p.last_edited.isoformat(),
                "created_time": p.created_time.isoformat(),
                "author": p.author,
                "archived": p.archived,
            }
            for p in pages
        ],
    }


@router.post("/connect")
async def connect_notion(
    payload: NotionConnectRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    integration = await service.connect_notion(current_user, payload.project_id, payload.code)
    return {"status": "success", "integration_id": integration.id}


@router.get("/workspaces")
async def list_workspaces(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    await service.require_project_membership(current_user, project_id, ProjectRole.VIEWER)

    integration = await service.integrations.get_by_project_and_provider(project_id, "notion")
    if not integration:
        return {"workspaces": []}

    pages = await service.list_notion_pages(current_user, project_id)
    return {
        "workspaces": [
            {
                "id": integration.workspace_id,
                "name": integration.workspace_name,
                "icon": integration.workspace_icon,
                "status": integration.status.value,
                "last_sync": integration.last_sync.isoformat() if integration.last_sync else None,
                "last_error": integration.last_error,
                "total_pages": len(pages),
            }
        ]
    }


@router.get("/pages")
async def list_pages(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    pages = await service.list_notion_pages(current_user, project_id)
    return {
        "pages": [
            {
                "id": str(p.id),
                "notion_page_id": p.notion_page_id,
                "parent_id": p.parent_id,
                "title": p.title,
                "url": p.url,
                "last_edited": p.last_edited.isoformat(),
                "created_time": p.created_time.isoformat(),
                "author": p.author,
                "archived": p.archived,
            }
            for p in pages
        ]
    }


@router.post("/sync")
async def sync_notion(
    payload: SyncRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    await service.sync_notion(current_user, payload.project_id)
    return {"status": "success"}


@router.delete("/disconnect")
async def disconnect_notion(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    await service.disconnect_notion(current_user, project_id)
    return {"status": "success"}
