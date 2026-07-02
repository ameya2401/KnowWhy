from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.github_client import GitHubAPIClient
from app.integrations.normalizer import GitHubNormalizer, NotionNormalizer
from app.integrations.notion_client import NotionAPIClient
from app.integrations.security import decrypt_credentials, encrypt_credentials
from app.models.integration import (
    Integration,
    IntegrationProvider,
    IntegrationRepository,
    IntegrationStatus,
    NotionPage,
)
from app.models.organization import OrganizationRole
from app.models.project import ProjectMember, ProjectRole
from app.models.user import User
from app.organizations.service import OrganizationService
from app.projects.permissions import has_project_role_at_least
from app.repositories.integrations import IntegrationRepository as DBIntegrationRepo
from app.repositories.integrations import IntegrationRepositoryRepository as DBRepoRepo
from app.repositories.integrations import SyncDataRepository
from app.repositories.projects import ProjectMemberRepository, ProjectRepository


class IntegrationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.integrations = DBIntegrationRepo(session)
        self.repos = DBRepoRepo(session)
        self.sync_data = SyncDataRepository(session)
        self.projects = ProjectRepository(session)
        self.project_members = ProjectMemberRepository(session)
        self.org_service = OrganizationService(session)
        self.normalizer = GitHubNormalizer()
        self.notion_normalizer = NotionNormalizer()

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

    async def connect_github(self, current_user: User, project_id: UUID, code: str) -> Integration:
        # Check permissions - must be Owner or Maintainer to connect integrations
        await self.require_project_membership(current_user, project_id, ProjectRole.MAINTAINER)

        project = await self.projects.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        # Verify active organization membership
        await self.org_service.require_membership(
            current_user, project.organization_id, minimum_role=OrganizationRole.MEMBER
        )

        try:
            access_token = await GitHubAPIClient.exchange_code_for_token(code)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange OAuth code: {str(e)}",
            ) from e

        # Test token validity & retrieve basic info
        try:
            client = GitHubAPIClient(access_token)
            user_info = await client.get_user_info()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub token validation failed: {str(e)}",
            ) from e

        # Encrypt the token securely
        credentials_data = {
            "access_token": access_token,
            "github_username": user_info.get("login"),
        }
        encrypted_creds = encrypt_credentials(credentials_data)

        # Check if integration already exists
        existing = await self.integrations.get_by_project_and_provider(project_id, "github")
        if existing:
            existing.status = IntegrationStatus.CONNECTED
            existing.credentials = encrypted_creds
            existing.connected_by_id = current_user.id
            existing.connected_at = datetime.now(UTC)
            existing.last_error = None
            integration = existing
        else:
            integration = Integration(
                organization_id=project.organization_id,
                project_id=project_id,
                provider=IntegrationProvider.GITHUB,
                status=IntegrationStatus.CONNECTED,
                credentials=encrypted_creds,
                connected_by_id=current_user.id,
                connected_at=datetime.now(UTC),
            )
            await self.integrations.create(integration)

        await self.session.commit()
        return integration

    async def disconnect_github(self, current_user: User, project_id: UUID) -> None:
        # Check permissions - must be Owner or Maintainer to disconnect
        await self.require_project_membership(current_user, project_id, ProjectRole.MAINTAINER)

        integration = await self.integrations.get_by_project_and_provider(project_id, "github")
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found.")

        await self.integrations.delete(integration)
        await self.session.commit()

    async def list_github_repositories(self, current_user: User, project_id: UUID) -> list[dict]:
        # Any project member can view the list of available repositories
        await self.require_project_membership(current_user, project_id, ProjectRole.VIEWER)

        integration = await self.integrations.get_by_project_and_provider(project_id, "github")
        if not integration or not integration.credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub integration not connected for this project.",
            )

        creds = decrypt_credentials(integration.credentials)
        token = creds.get("access_token")

        try:
            client = GitHubAPIClient(token)
            repos = await client.list_repositories()
            return repos
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"GitHub API error: {str(e)}",
            ) from e

    async def connect_repository(
        self,
        current_user: User,
        project_id: UUID,
        github_repo_id: str,
        name: str,
        owner: str,
        default_branch: str,
        visibility: str,
        clone_url: str,
    ) -> IntegrationRepository:
        await self.require_project_membership(current_user, project_id, ProjectRole.MAINTAINER)

        integration = await self.integrations.get_by_project_and_provider(project_id, "github")
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub integration not connected for this project.",
            )

        existing_repo = await self.repos.get_by_integration_and_github_id(
            integration.id, github_repo_id
        )
        if existing_repo:
            existing_repo.name = name
            existing_repo.owner = owner
            existing_repo.default_branch = default_branch
            existing_repo.visibility = visibility
            existing_repo.clone_url = clone_url
            repo = existing_repo
        else:
            repo = IntegrationRepository(
                integration_id=integration.id,
                github_repo_id=github_repo_id,
                name=name,
                owner=owner,
                default_branch=default_branch,
                visibility=visibility,
                clone_url=clone_url,
            )
            await self.repos.create(repo)

        await self.session.commit()
        return repo

    async def sync_integration(self, current_user: User, project_id: UUID) -> None:
        await self.require_project_membership(current_user, project_id, ProjectRole.VIEWER)

        integration = await self.integrations.get_by_project_and_provider(project_id, "github")
        if not integration or not integration.credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub integration not connected for this project.",
            )

        integration.status = IntegrationStatus.SYNCING
        await self.session.commit()

        creds = decrypt_credentials(integration.credentials)
        token = creds.get("access_token")
        client = GitHubAPIClient(token)

        try:
            connected_repos = await self.repos.list_for_integration(integration.id)
            for repo in connected_repos:
                # 1. Sync Commits
                try:
                    commits_raw = await client.list_commits(repo.owner, repo.name)
                    for raw_commit in commits_raw:
                        normalized = self.normalizer.normalize_commit(repo.id, raw_commit)
                        exists = await self.sync_data.get_commit_by_sha(repo.id, normalized.sha)
                        if not exists:
                            await self.sync_data.create_commit(normalized)
                except Exception as commit_err:
                    print(f"Error syncing commits for {repo.owner}/{repo.name}: {commit_err}")

                # 2. Sync Pull Requests
                try:
                    prs_raw = await client.list_pull_requests(repo.owner, repo.name)
                    for raw_pr in prs_raw:
                        normalized = self.normalizer.normalize_pull_request(repo.id, raw_pr)
                        exists = await self.sync_data.get_pull_request_by_github_id(
                            repo.id, normalized.github_pr_id
                        )
                        if not exists:
                            await self.sync_data.create_pull_request(normalized)
                except Exception as pr_err:
                    print(f"Error syncing PRs for {repo.owner}/{repo.name}: {pr_err}")

                # 3. Sync Issues
                try:
                    issues_raw = await client.list_issues(repo.owner, repo.name)
                    for raw_issue in issues_raw:
                        normalized = self.normalizer.normalize_issue(repo.id, raw_issue)
                        exists = await self.sync_data.get_issue_by_github_id(
                            repo.id, normalized.github_issue_id
                        )
                        if not exists:
                            await self.sync_data.create_issue(normalized)
                except Exception as issue_err:
                    print(f"Error syncing Issues for {repo.owner}/{repo.name}: {issue_err}")

                repo.last_sync = datetime.now(UTC)

            integration.status = IntegrationStatus.CONNECTED
            integration.last_sync = datetime.now(UTC)
            integration.last_error = None
        except Exception as e:
            integration.status = IntegrationStatus.ERROR
            integration.last_error = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Synchronization failed: {str(e)}",
            ) from e
        finally:
            await self.session.commit()

    async def connect_notion(self, current_user: User, project_id: UUID, code: str) -> Integration:
        await self.require_project_membership(current_user, project_id, ProjectRole.MAINTAINER)

        project = await self.projects.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        await self.org_service.require_membership(
            current_user, project.organization_id, minimum_role=OrganizationRole.MEMBER
        )

        try:
            oauth_data = await NotionAPIClient.exchange_code_for_token(code)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange Notion OAuth code: {str(e)}",
            ) from e

        access_token = oauth_data.get("access_token")
        workspace_id = oauth_data.get("workspace_id")
        workspace_name = oauth_data.get("workspace_name", "Notion Workspace")
        workspace_icon = oauth_data.get("workspace_icon")

        credentials_data = {
            "access_token": access_token,
            "workspace_id": workspace_id,
            "workspace_name": workspace_name,
        }
        encrypted_creds = encrypt_credentials(credentials_data)

        existing = await self.integrations.get_by_project_and_provider(project_id, "notion")
        if existing:
            existing.status = IntegrationStatus.CONNECTED
            existing.credentials = encrypted_creds
            existing.workspace_id = workspace_id
            existing.workspace_name = workspace_name
            existing.workspace_icon = workspace_icon
            existing.connected_by_id = current_user.id
            existing.connected_at = datetime.now(UTC)
            existing.last_error = None
            integration = existing
        else:
            integration = Integration(
                organization_id=project.organization_id,
                project_id=project_id,
                provider=IntegrationProvider.NOTION,
                status=IntegrationStatus.CONNECTED,
                credentials=encrypted_creds,
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                workspace_icon=workspace_icon,
                connected_by_id=current_user.id,
                connected_at=datetime.now(UTC),
            )
            await self.integrations.create(integration)

        await self.session.commit()
        return integration

    async def disconnect_notion(self, current_user: User, project_id: UUID) -> None:
        await self.require_project_membership(current_user, project_id, ProjectRole.MAINTAINER)

        integration = await self.integrations.get_by_project_and_provider(project_id, "notion")
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found.")

        await self.integrations.delete(integration)
        await self.session.commit()

    async def list_notion_pages(self, current_user: User, project_id: UUID) -> list[NotionPage]:
        await self.require_project_membership(current_user, project_id, ProjectRole.VIEWER)

        integration = await self.integrations.get_by_project_and_provider(project_id, "notion")
        if not integration:
            return []

        return await self.sync_data.list_notion_pages_for_integration(integration.id)

    async def sync_notion(self, current_user: User, project_id: UUID) -> None:
        await self.require_project_membership(current_user, project_id, ProjectRole.VIEWER)

        integration = await self.integrations.get_by_project_and_provider(project_id, "notion")
        if not integration or not integration.credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notion integration not connected for this project.",
            )

        integration.status = IntegrationStatus.SYNCING
        await self.session.commit()

        creds = decrypt_credentials(integration.credentials)
        token = creds.get("access_token")
        client = NotionAPIClient(token)

        try:
            results = await client.search()
            for raw_page in results:
                normalized = self.notion_normalizer.normalize_page(integration.id, raw_page)
                exists = await self.sync_data.get_notion_page_by_notion_id(
                    integration.id, normalized.notion_page_id
                )
                if exists:
                    if exists.last_edited < normalized.last_edited:
                        exists.title = normalized.title
                        exists.url = normalized.url
                        exists.parent_id = normalized.parent_id
                        exists.last_edited = normalized.last_edited
                        exists.archived = normalized.archived
                        exists.author = normalized.author
                else:
                    await self.sync_data.create_notion_page(normalized)

            integration.status = IntegrationStatus.CONNECTED
            integration.last_sync = datetime.now(UTC)
            integration.last_error = None
        except Exception as e:
            integration.status = IntegrationStatus.ERROR
            integration.last_error = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Synchronization failed: {str(e)}",
            ) from e
        finally:
            await self.session.commit()
