import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integration import Commit, DriveFile, Issue, NotionPage, PullRequest
from app.models.knowledge import KnowledgeItem, KnowledgeRelationship, KnowledgeSyncLog
from app.repositories.integrations import (
    IntegrationRepository,
    IntegrationRepositoryRepository,
    SyncDataRepository,
)
from app.repositories.knowledge import KnowledgeRepository


class NormalizationEngine:
    """Utility engine to transform integration models into unified KnowledgeItem models."""

    @staticmethod
    def normalize_commit(org_id: UUID, proj_id: UUID, commit: Commit) -> KnowledgeItem:
        title = commit.message.split("\n")[0] if commit.message else "Commit"
        if len(title) > 100:
            title = title[:97] + "..."

        return KnowledgeItem(
            organization_id=org_id,
            project_id=proj_id,
            source="github",
            source_entity_id=commit.sha,
            entity_type="commit",
            title=title,
            description=commit.message,
            content=commit.message,
            url=None,  # Commit URL is not stored but can be reconstructed
            author=commit.author_name,
            created_time=commit.commit_date,
            updated_time=commit.commit_date,
            metadata_json={
                "sha": commit.sha,
                "author_email": commit.author_email,
            },
            tags=["github", "commit"],
            status="active",
        )

    @staticmethod
    def normalize_pull_request(org_id: UUID, proj_id: UUID, pr: PullRequest) -> KnowledgeItem:
        updated_time = pr.merged_at or pr.closed_at or pr.created_at_meta
        return KnowledgeItem(
            organization_id=org_id,
            project_id=proj_id,
            source="github",
            source_entity_id=pr.github_pr_id,
            entity_type="pull_request",
            title=f"#{pr.number} {pr.title}",
            description=f"Pull Request #{pr.number} (State: {pr.state})",
            content=f"Author: {pr.author}\nState: {pr.state}",
            url=None,
            author=pr.author,
            created_time=pr.created_at_meta,
            updated_time=updated_time,
            metadata_json={
                "number": pr.number,
                "state": pr.state,
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
            },
            tags=["github", "pull_request", pr.state],
            status="active",
        )

    @staticmethod
    def normalize_issue(org_id: UUID, proj_id: UUID, issue: Issue) -> KnowledgeItem:
        updated_time = issue.closed_at or issue.created_at_meta
        return KnowledgeItem(
            organization_id=org_id,
            project_id=proj_id,
            source="github",
            source_entity_id=issue.github_issue_id,
            entity_type="issue",
            title=f"#{issue.number} {issue.title}",
            description=f"Issue #{issue.number} (State: {issue.state})",
            content=f"Author: {issue.author}\nState: {issue.state}",
            url=None,
            author=issue.author,
            created_time=issue.created_at_meta,
            updated_time=updated_time,
            metadata_json={
                "number": issue.number,
                "state": issue.state,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            },
            tags=["github", "issue", issue.state],
            status="active",
        )

    @staticmethod
    def normalize_notion_page(org_id: UUID, proj_id: UUID, page: NotionPage) -> KnowledgeItem:
        return KnowledgeItem(
            organization_id=org_id,
            project_id=proj_id,
            source="notion",
            source_entity_id=page.notion_page_id,
            entity_type="notion_page",
            title=page.title,
            description=f"Notion page: {page.title}",
            content=f"Author: {page.author or 'Unknown'}",
            url=page.url,
            author=page.author,
            created_time=page.created_time,
            updated_time=page.last_edited,
            metadata_json={
                "parent_id": page.parent_id,
                "archived": page.archived,
            },
            tags=["notion", "page"],
            status="active" if not page.archived else "archived",
        )

    @staticmethod
    def normalize_drive_file(org_id: UUID, proj_id: UUID, file: DriveFile) -> KnowledgeItem:
        is_folder = file.mime_type == "application/vnd.google-apps.folder"
        entity_type = "folder" if is_folder else "document"
        return KnowledgeItem(
            organization_id=org_id,
            project_id=proj_id,
            source="google_drive",
            source_entity_id=file.google_file_id,
            entity_type=entity_type,
            title=file.name,
            description=f"Google Drive file: {file.name} ({file.mime_type})",
            content=file.content,
            url=file.url,
            author=file.owner,
            created_time=file.created_time,
            updated_time=file.modified_time,
            metadata_json={
                "mime_type": file.mime_type,
                "parent_folder": file.parent_folder,
                "file_size": file.file_size,
                "archived": file.archived,
            },
            tags=["google_drive", entity_type],
            status="active" if not file.archived else "archived",
        )


class KnowledgeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.knowledge_repo = KnowledgeRepository(session)
        self.integration_repo = IntegrationRepository(session)
        self.repo_repo = IntegrationRepositoryRepository(session)
        self.sync_data_repo = SyncDataRepository(session)

    async def list_items(
        self,
        project_id: UUID,
        source: str | None = None,
        entity_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[KnowledgeItem], int]:
        return await self.knowledge_repo.list_items(
            project_id=project_id,
            source=source,
            entity_type=entity_type,
            status=status,
            search=search,
            limit=limit,
            offset=offset,
        )

    async def get_item_by_id(self, item_id: UUID) -> KnowledgeItem | None:
        return await self.knowledge_repo.get_item_by_id(item_id)

    async def list_relationships(self, item_id: UUID) -> list[KnowledgeRelationship]:
        return await self.knowledge_repo.list_relationships(item_id)

    async def get_timeline(
        self,
        project_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeItem]:
        return await self.knowledge_repo.get_timeline(project_id, limit, offset)

    async def get_latest_sync_log(self, project_id: UUID) -> KnowledgeSyncLog | None:
        return await self.knowledge_repo.get_latest_sync_log(project_id)

    async def sync_project_knowledge(self, project_id: UUID) -> KnowledgeSyncLog:
        """Collect all sync items from integrations, normalize, save, and map relationships."""
        log = KnowledgeSyncLog(
            project_id=project_id,
            started_at=datetime.now(UTC),
            status="running",
            items_synced=0,
            relationships_created=0,
        )
        await self.knowledge_repo.create_sync_log(log)
        await self.session.commit()

        try:
            # 1. Fetch integrations for project
            github_integration = await self.integration_repo.get_by_project_and_provider(
                project_id, "github"
            )
            notion_integration = await self.integration_repo.get_by_project_and_provider(
                project_id, "notion"
            )
            drive_integration = await self.integration_repo.get_by_project_and_provider(
                project_id, "google_drive"
            )

            items_count = 0
            relationships_count = 0

            # Map to lookup existing items during relationship mapping
            # Key: (source, source_entity_id), Value: KnowledgeItem
            items_by_source_key: dict[tuple[str, str], KnowledgeItem] = {}

            async def save_or_update_item(item: KnowledgeItem) -> KnowledgeItem:
                nonlocal items_count
                exists = await self.knowledge_repo.get_item_by_source_id(
                    item.project_id, item.source, item.source_entity_id
                )
                if exists:
                    # Update fields if modified time is newer
                    if exists.updated_time <= item.updated_time:
                        exists.title = item.title
                        exists.description = item.description
                        exists.content = item.content
                        exists.url = item.url
                        exists.author = item.author
                        exists.updated_time = item.updated_time
                        exists.metadata_json = item.metadata_json
                        exists.tags = item.tags
                        exists.status = item.status
                    items_by_source_key[(exists.source, exists.source_entity_id)] = exists
                    return exists
                else:
                    saved = await self.knowledge_repo.create_item(item)
                    items_count += 1
                    items_by_source_key[(saved.source, saved.source_entity_id)] = saved
                    return saved

            # Normalize GitHub items
            if github_integration:
                org_id = github_integration.organization_id
                repos = await self.repo_repo.list_for_integration(github_integration.id)
                for repo in repos:
                    # Get commits
                    commits_res = await self.session.execute(
                        select(Commit).where(Commit.repository_id == repo.id)
                    )
                    for commit in commits_res.scalars().all():
                        norm_item = NormalizationEngine.normalize_commit(org_id, project_id, commit)
                        await save_or_update_item(norm_item)

                    # Get PRs
                    prs_res = await self.session.execute(
                        select(PullRequest).where(PullRequest.repository_id == repo.id)
                    )
                    for pr in prs_res.scalars().all():
                        norm_item = NormalizationEngine.normalize_pull_request(
                            org_id, project_id, pr
                        )
                        await save_or_update_item(norm_item)

                    # Get Issues
                    issues_res = await self.session.execute(
                        select(Issue).where(Issue.repository_id == repo.id)
                    )
                    for issue in issues_res.scalars().all():
                        norm_item = NormalizationEngine.normalize_issue(org_id, project_id, issue)
                        await save_or_update_item(norm_item)

            # Normalize Notion items
            if notion_integration:
                org_id = notion_integration.organization_id
                pages_res = await self.session.execute(
                    select(NotionPage).where(NotionPage.integration_id == notion_integration.id)
                )
                for page in pages_res.scalars().all():
                    norm_item = NormalizationEngine.normalize_notion_page(org_id, project_id, page)
                    await save_or_update_item(norm_item)

            # Normalize Google Drive items
            if drive_integration:
                org_id = drive_integration.organization_id
                files_res = await self.session.execute(
                    select(DriveFile).where(DriveFile.integration_id == drive_integration.id)
                )
                for file in files_res.scalars().all():
                    norm_item = NormalizationEngine.normalize_drive_file(org_id, project_id, file)
                    await save_or_update_item(norm_item)

            # Flush to ensure IDs are available
            await self.session.flush()

            # 2. Build Relationships
            async def add_relationship(
                source_id: UUID, target_id: UUID, rel_type: str, conf: float = 1.0
            ):
                nonlocal relationships_count
                exists_rel = await self.knowledge_repo.get_relationship(
                    source_id, target_id, rel_type
                )
                if not exists_rel:
                    rel = KnowledgeRelationship(
                        source_item_id=source_id,
                        target_item_id=target_id,
                        relationship_type=rel_type,
                        confidence=conf,
                    )
                    await self.knowledge_repo.create_relationship(rel)
                    relationships_count += 1

            # Notion & Google Drive Parent-Child relationships
            for item in list(items_by_source_key.values()):
                if item.source == "notion":
                    parent_id = item.metadata_json.get("parent_id")
                    if parent_id:
                        parent_item = items_by_source_key.get(("notion", parent_id))
                        if parent_item:
                            await add_relationship(parent_item.id, item.id, "contains")

                elif item.source == "google_drive":
                    parent_folder = item.metadata_json.get("parent_folder")
                    if parent_folder:
                        parent_item = items_by_source_key.get(("google_drive", parent_folder))
                        if parent_item:
                            await add_relationship(parent_item.id, item.id, "contains")

                elif item.source == "github" and item.entity_type == "commit":
                    # Parse commit message for issue/PR links (e.g. "fixes #12")
                    text = item.description or ""
                    # Match any hashtag issue number like #12
                    matches = re.findall(r"#(\d+)", text)
                    for match in set(matches):
                        issue_num = int(match)
                        # Look for github issue or PR with this number under same project
                        for other in list(items_by_source_key.values()):
                            if other.source == "github" and other.entity_type in (
                                "issue",
                                "pull_request",
                            ):
                                if other.metadata_json.get("number") == issue_num:
                                    # Create references relationship
                                    await add_relationship(item.id, other.id, "references")

                elif item.source == "github" and item.entity_type == "pull_request":
                    # Parse PR titles / descriptions for issue links
                    text = f"{item.title} {item.description or ''}"
                    matches = re.findall(r"#(\d+)", text)
                    for match in set(matches):
                        issue_num = int(match)
                        for other in list(items_by_source_key.values()):
                            if other.source == "github" and other.entity_type == "issue":
                                if other.metadata_json.get("number") == issue_num:
                                    # Create fixes relationship
                                    await add_relationship(item.id, other.id, "fixes")

            # Update log
            log.status = "completed"
            log.completed_at = datetime.now(UTC)
            log.items_synced = items_count
            log.relationships_created = relationships_count
            await self.session.commit()
            return log

        except Exception as err:
            log.status = "failed"
            log.completed_at = datetime.now(UTC)
            log.error_message = str(err)
            await self.session.commit()
            raise err
