from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.knowledge import KnowledgeItem
from app.models.user import User
from app.repositories.search import SearchRepository
from app.services.query_processor import QueryProcessor
from app.services.search import SearchService
from app.services.search_fusion import ReciprocalRankFusion, WeightedReRanker


@pytest.fixture
def sample_user() -> User:
    return User(
        id=uuid4(),
        email="searcher@example.com",
        full_name="Alice Searcher",
    )


@pytest.fixture
def mock_db_session() -> AsyncMock:
    return AsyncMock()


@pytest.mark.asyncio
async def test_search_repository_ranking_logic(mock_db_session):
    repo = SearchRepository(mock_db_session)
    project_id = uuid4()

    item1 = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        organization_id=uuid4(),
        source="github",
        source_entity_id="c1",
        entity_type="commit",
        title="Fix database migration index bug",
        content="We need to create index for title and content fields.",
        author="Alice Coder",
        created_time=datetime.now(UTC),
        updated_time=datetime.now(UTC),
        tags=["database", "bug"],
        status="active",
    )
    item2 = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        organization_id=uuid4(),
        source="notion",
        source_entity_id="p1",
        entity_type="notion_page",
        title="Release Guidelines",
        content="Guidelines for database indices.",
        author="Bob Admin",
        created_time=datetime.now(UTC) - timedelta(days=2),
        updated_time=datetime.now(UTC) - timedelta(days=2),
        tags=["release", "documentation"],
        status="active",
    )

    count_res = MagicMock()
    count_res.scalar_one.return_value = 2

    items_res = MagicMock()
    items_res.all.return_value = [(item1, 120.0), (item2, 10.0)]

    async def mock_execute(stmt):
        stmt_str = str(stmt)
        if "count" in stmt_str:
            return count_res
        return items_res

    mock_db_session.execute.side_effect = mock_execute

    results, total = await repo.search(
        project_id=project_id,
        q="database migration",
        sort_by="relevance",
        limit=10,
        offset=0,
    )

    assert total == 2
    assert len(results) == 2
    assert results[0][0].title == "Fix database migration index bug"
    assert results[0][1] == 120.0
    assert results[1][0].title == "Release Guidelines"
    assert results[1][1] == 10.0


@pytest.mark.asyncio
async def test_search_service_recent_and_suggestions(mock_db_session, sample_user):
    service = SearchService(mock_db_session)
    project_id = uuid4()

    suggestions_res = MagicMock()
    suggestions_res.scalars.return_value.all.return_value = ["Fix database migration index bug"]
    mock_db_session.execute.return_value = suggestions_res

    suggestions = await service.get_suggestions(project_id, q="database")
    assert len(suggestions) == 1
    assert suggestions[0] == "Fix database migration index bug"

    recent = await service.get_recent_searches(sample_user.id, project_id)
    assert isinstance(recent, list)


@pytest.mark.asyncio
async def test_available_filters(mock_db_session):
    repo = SearchRepository(mock_db_session)
    project_id = uuid4()

    sources_res = MagicMock()
    sources_res.scalars.return_value.all.return_value = ["github", "notion"]

    types_res = MagicMock()
    types_res.scalars.return_value.all.return_value = ["commit", "notion_page"]

    authors_res = MagicMock()
    authors_res.scalars.return_value.all.return_value = ["Alice Coder", "Bob Admin"]

    tags_res = MagicMock()
    tags_res.scalars.return_value.all.return_value = [["database", "bug"], ["release"]]

    async def mock_execute(stmt):
        stmt_str = str(stmt)
        res = MagicMock()
        if "source" in stmt_str:
            return sources_res
        elif "entity_type" in stmt_str:
            return types_res
        elif "author" in stmt_str:
            return authors_res
        elif "tags" in stmt_str:
            return tags_res
        return res

    mock_db_session.execute.side_effect = mock_execute

    filters = await repo.get_available_filters(project_id)
    assert filters["sources"] == ["github", "notion"]
    assert filters["entity_types"] == ["commit", "notion_page"]
    assert filters["authors"] == ["Alice Coder", "Bob Admin"]
    assert set(filters["tags"]) == {"database", "bug", "release"}


def test_query_processor():
    processed = QueryProcessor.process('why did we "adopt fastapi" in postgresql?')
    assert "fastapi" in processed["tokens"]
    assert "postgresql" in processed["tokens"]
    assert "adopt fastapi" in processed["phrases"]
    assert "did" not in processed["tokens"]


def test_rrf_and_reranking():
    project_id = uuid4()
    item1 = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        source="github",
        title="FastAPI adoption decision",
        updated_time=datetime.now(UTC),
    )
    item2 = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        source="notion",
        title="Postgres setup guide",
        updated_time=datetime.now(UTC) - timedelta(days=5),
    )

    lexical_results = [(item1, 50.0)]
    semantic_results = [(item2, 0.8), (item1, 0.6)]

    fused = ReciprocalRankFusion(k=60).fuse(lexical_results, semantic_results)
    assert len(fused) == 2
    assert fused[0][0].id == item1.id

    re_ranked = WeightedReRanker().re_rank(fused)
    assert len(re_ranked) == 2
    assert re_ranked[0][1] > 0.0


@pytest.mark.asyncio
async def test_hybrid_search_service(mock_db_session, sample_user):
    service = SearchService(mock_db_session)
    project_id = uuid4()

    service.embedding_service.provider.get_embeddings = AsyncMock(return_value=[[0.1] * 1536])

    item = KnowledgeItem(
        id=uuid4(),
        project_id=project_id,
        organization_id=uuid4(),
        source="notion",
        source_entity_id="p1",
        entity_type="notion_page",
        title="Postgres Setup Guide",
        content="Setup guidelines.",
        author="Alice",
        created_time=datetime.now(UTC),
        updated_time=datetime.now(UTC),
        tags=["database"],
        status="active",
    )

    service.search_repo.search = AsyncMock(return_value=([(item, 100.0)], 1))
    service.search_repo.semantic_search = AsyncMock(return_value=[(item, 0.9)])

    output = await service.hybrid_search(
        project_id=project_id, user_id=sample_user.id, q="postgres setup", limit=10, offset=0
    )

    assert output["total"] == 1
    assert output["results"][0]["item"]["title"] == "Postgres Setup Guide"
    assert output["results"][0]["match_type"] == "hybrid"
    assert output["results"][0]["explanation"]["semantic_score"] == 0.9
