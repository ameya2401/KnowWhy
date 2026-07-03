from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.integration import Commit, DriveFile, Integration, Issue, NotionPage, PullRequest
from app.services.knowledge import KnowledgeService, NormalizationEngine


def test_normalization_engine():
    org_id = uuid4()
    proj_id = uuid4()

    # 1. Commit
    commit = Commit(
        id=uuid4(),
        repository_id=uuid4(),
        sha="abcdef123456",
        author_name="Alice coder",
        author_email="alice@code.com",
        message="Fix layout bug\n\nDetailed explanation",
        commit_date=datetime.now(UTC),
    )
    item = NormalizationEngine.normalize_commit(org_id, proj_id, commit)
    assert item.source == "github"
    assert item.source_entity_id == "abcdef123456"
    assert item.entity_type == "commit"
    assert item.title == "Fix layout bug"
    assert item.author == "Alice coder"

    # 2. Pull Request
    pr = PullRequest(
        id=uuid4(),
        repository_id=uuid4(),
        github_pr_id="pr_999",
        number=42,
        title="Add settings menu",
        state="open",
        author="bob",
        created_at_meta=datetime.now(UTC),
    )
    item = NormalizationEngine.normalize_pull_request(org_id, proj_id, pr)
    assert item.source == "github"
    assert item.source_entity_id == "pr_999"
    assert item.entity_type == "pull_request"
    assert "#42" in item.title
    assert item.author == "bob"

    # 3. Notion Page
    notion_page = NotionPage(
        id=uuid4(),
        integration_id=uuid4(),
        notion_page_id="notion_page_123",
        title="Project Specs",
        url="http://notion.so/specs",
        last_edited=datetime.now(UTC),
        created_time=datetime.now(UTC),
        author="Charlie",
        archived=False,
    )
    item = NormalizationEngine.normalize_notion_page(org_id, proj_id, notion_page)
    assert item.source == "notion"
    assert item.source_entity_id == "notion_page_123"
    assert item.title == "Project Specs"
    assert item.url == "http://notion.so/specs"

    # 4. Google Drive File
    drive_file = DriveFile(
        id=uuid4(),
        integration_id=uuid4(),
        google_file_id="drive_file_456",
        name="Resume.pdf",
        mime_type="application/pdf",
        owner="David",
        url="http://drive.google.com/resume",
        created_time=datetime.now(UTC),
        modified_time=datetime.now(UTC),
        archived=False,
        content="This is the file content",
    )
    item = NormalizationEngine.normalize_drive_file(org_id, proj_id, drive_file)
    assert item.source == "google_drive"
    assert item.entity_type == "document"
    assert item.title == "Resume.pdf"
    assert item.content == "This is the file content"


@pytest.mark.asyncio
async def test_knowledge_service_sync():
    session = AsyncMock()
    service = KnowledgeService(session)

    project_id = uuid4()
    org_id = uuid4()

    # Create dummy integrations
    github_integration = Integration(
        id=uuid4(), organization_id=org_id, project_id=project_id, provider="github"
    )
    notion_integration = Integration(
        id=uuid4(), organization_id=org_id, project_id=project_id, provider="notion"
    )

    # Mock repositories
    service.integration_repo.get_by_project_and_provider = AsyncMock(
        side_effect=lambda pid, provider: {
            "github": github_integration,
            "notion": notion_integration,
            "google_drive": None,
        }.get(provider)
    )

    # Mock github repo listing
    repo_mock = MagicMock()
    repo_mock.id = uuid4()
    service.repo_repo.list_for_integration = AsyncMock(return_value=[repo_mock])

    # Mock DB Query Results
    # Commits
    commit_mock = Commit(
        id=uuid4(),
        repository_id=repo_mock.id,
        sha="c1",
        author_name="Alice",
        message="Resolves #55",
        commit_date=datetime.now(UTC),
    )
    # Issue
    issue_mock = Issue(
        id=uuid4(),
        repository_id=repo_mock.id,
        github_issue_id="i55",
        number=55,
        title="Bug in CSS styling",
        state="open",
        author="Alice",
        created_at_meta=datetime.now(UTC),
    )
    # Notion Page
    page_mock = NotionPage(
        id=uuid4(),
        integration_id=notion_integration.id,
        notion_page_id="p1",
        title="Page 1",
        url="http://notion.so/p1",
        last_edited=datetime.now(UTC),
        created_time=datetime.now(UTC),
        author="Charlie",
        archived=False,
    )

    # Mock database session execution scalars
    commits_list_mock = MagicMock()
    commits_list_mock.scalars.return_value.all.return_value = [commit_mock]

    issues_list_mock = MagicMock()
    issues_list_mock.scalars.return_value.all.return_value = [issue_mock]

    pages_list_mock = MagicMock()
    pages_list_mock.scalars.return_value.all.return_value = [page_mock]

    # Map the execute responses
    async def mock_execute(stmt):
        stmt_str = str(stmt)
        res = MagicMock()
        if "integration_commits" in stmt_str:
            return commits_list_mock
        elif "integration_issues" in stmt_str:
            return issues_list_mock
        elif "notion_pages" in stmt_str:
            return pages_list_mock
        return res

    session.execute = AsyncMock(side_effect=mock_execute)

    # Mock knowledge_repo methods
    created_items = []
    created_relationships = []

    async def mock_create_item(item):
        item.id = uuid4()
        created_items.append(item)
        return item

    async def mock_get_item_by_source_id(pid, source, s_id):
        for i in created_items:
            if i.project_id == pid and i.source == source and i.source_entity_id == s_id:
                return i
        return None

    async def mock_create_relationship(rel):
        rel.id = uuid4()
        created_relationships.append(rel)
        return rel

    async def mock_get_relationship(s_id, t_id, r_type):
        for r in created_relationships:
            if (
                r.source_item_id == s_id
                and r.target_item_id == t_id
                and r.relationship_type == r_type
            ):
                return r
        return None

    service.knowledge_repo.create_item = AsyncMock(side_effect=mock_create_item)
    service.knowledge_repo.get_item_by_source_id = AsyncMock(side_effect=mock_get_item_by_source_id)
    service.knowledge_repo.create_relationship = AsyncMock(side_effect=mock_create_relationship)
    service.knowledge_repo.get_relationship = AsyncMock(side_effect=mock_get_relationship)
    service.knowledge_repo.create_sync_log = AsyncMock()

    # Perform Sync
    log = await service.sync_project_knowledge(project_id)

    assert log.status == "completed"
    assert log.items_synced == 3  # Commit + Issue + Notion Page
    assert len(created_items) == 3

    # Check commit-issue relationship references link (resolves #55)
    assert log.relationships_created == 1
    assert len(created_relationships) == 1
    assert created_relationships[0].relationship_type == "references"
