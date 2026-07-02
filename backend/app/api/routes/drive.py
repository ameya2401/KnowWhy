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

router = APIRouter(prefix="/integrations/drive", tags=["integrations"])


class DriveConnectRequest(BaseModel):
    code: str
    project_id: UUID
    redirect_uri: str


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

    integration = await service.integrations.get_by_project_and_provider(project_id, "google_drive")
    if not integration:
        return {"connected": False, "integration": None, "files": []}

    files = await service.list_drive_files(current_user, project_id)
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
        "files": [
            {
                "id": str(f.id),
                "google_file_id": f.google_file_id,
                "parent_folder": f.parent_folder,
                "name": f.name,
                "mime_type": f.mime_type,
                "file_size": f.file_size,
                "owner": f.owner,
                "url": f.url,
                "created_time": f.created_time.isoformat(),
                "modified_time": f.modified_time.isoformat(),
                "last_sync": f.last_sync.isoformat() if f.last_sync else None,
                "archived": f.archived,
                "content": f.content,
            }
            for f in files
        ],
    }


@router.post("/connect")
async def connect_drive(
    payload: DriveConnectRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    integration = await service.connect_drive(
        current_user, payload.project_id, payload.code, payload.redirect_uri
    )
    return {"status": "success", "integration_id": integration.id}


@router.get("/files")
async def list_files(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    files = await service.list_drive_files(current_user, project_id)
    return {
        "files": [
            {
                "id": str(f.id),
                "google_file_id": f.google_file_id,
                "parent_folder": f.parent_folder,
                "name": f.name,
                "mime_type": f.mime_type,
                "file_size": f.file_size,
                "owner": f.owner,
                "url": f.url,
                "created_time": f.created_time.isoformat(),
                "modified_time": f.modified_time.isoformat(),
                "last_sync": f.last_sync.isoformat() if f.last_sync else None,
                "archived": f.archived,
                "content": f.content,
            }
            for f in files
        ]
    }


@router.get("/folders")
async def list_folders(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    folders = await service.list_drive_folders(current_user, project_id)
    return {"folders": folders}


@router.post("/sync")
async def sync_drive(
    payload: SyncRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    await service.sync_drive(current_user, payload.project_id)
    return {"status": "success"}


@router.delete("/disconnect")
async def disconnect_drive(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    await service.disconnect_drive(current_user, project_id)
    return {"status": "success"}
