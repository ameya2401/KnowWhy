import hashlib
import hmac
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.integrations.service import IntegrationService
from app.models.project import ProjectRole
from app.models.user import User

router = APIRouter(prefix="/integrations/github", tags=["integrations"])


class GitHubConnectRequest(BaseModel):
    code: str
    project_id: UUID


class ConnectRepositoryRequest(BaseModel):
    project_id: UUID
    github_repo_id: str
    name: str
    owner: str
    default_branch: str
    visibility: str
    clone_url: str


class SyncRequest(BaseModel):
    project_id: UUID


class DisconnectRequest(BaseModel):
    project_id: UUID


@router.get("")
async def get_integration(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    await service.require_project_membership(current_user, project_id, ProjectRole.VIEWER)

    integration = await service.integrations.get_by_project_and_provider(project_id, "github")
    if not integration:
        return {"connected": False, "integration": None, "repositories": []}

    repos = await service.repos.list_for_integration(integration.id)
    return {
        "connected": True,
        "integration": {
            "id": integration.id,
            "status": integration.status.value,
            "last_sync": integration.last_sync.isoformat() if integration.last_sync else None,
            "last_error": integration.last_error,
            "connected_at": integration.connected_at.isoformat(),
        },
        "repositories": [
            {
                "id": r.id,
                "github_repo_id": r.github_repo_id,
                "name": r.name,
                "owner": r.owner,
                "default_branch": r.default_branch,
                "visibility": r.visibility,
                "clone_url": r.clone_url,
                "last_sync": r.last_sync.isoformat() if r.last_sync else None,
            }
            for r in repos
        ],
    }


@router.post("/connect")
async def connect_github(
    payload: GitHubConnectRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    integration = await service.connect_github(current_user, payload.project_id, payload.code)
    return {"status": "success", "integration_id": integration.id}


@router.get("/repositories")
async def list_repositories(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    repos = await service.list_github_repositories(current_user, project_id)
    return {"repositories": repos}


@router.post("/repositories/{github_repo_id}/connect")
async def connect_repository(
    github_repo_id: str,
    payload: ConnectRepositoryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    # Verify path id matches payload id to prevent mismatches
    if github_repo_id != payload.github_repo_id:
        raise HTTPException(status_code=400, detail="Repository ID mismatch between path and body.")

    service = IntegrationService(db)
    repo = await service.connect_repository(
        current_user,
        payload.project_id,
        payload.github_repo_id,
        payload.name,
        payload.owner,
        payload.default_branch,
        payload.visibility,
        payload.clone_url,
    )
    return {"status": "success", "repository_id": repo.id}


@router.post("/sync")
async def sync_integration(
    payload: SyncRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    await service.sync_integration(current_user, payload.project_id)
    return {"status": "success"}


@router.delete("/disconnect")
async def disconnect_github(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    service = IntegrationService(db)
    await service.disconnect_github(current_user, project_id)
    return {"status": "success"}


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_database_session)],
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
):
    body = await request.body()

    # Optional signature verification using github client secret as webhook secret
    if settings.github_client_secret and x_hub_signature_256:
        signature = (
            "sha256="
            + hmac.new(
                settings.github_client_secret.encode("utf-8"),
                body,
                hashlib.sha256,
            ).hexdigest()
        )
        if not hmac.compare_digest(signature, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse event type from header
    event_type = request.headers.get("X-GitHub-Event", "ping")

    # Webhook handling placeholder: print or log the webhook details.
    # Supported events: ping, push, pull_request, issues
    print(f"Received GitHub webhook event: {event_type}")

    # Return 200 OK
    return Response(status_code=status.HTTP_200_OK)
