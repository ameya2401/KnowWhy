from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.knowledge import KnowledgeItem
from app.services.embedding_queue import EmbeddingQueueService, ProjectQueueState
from app.services.embeddings import ChunkingEngine, EmbeddingService, MockEmbeddingProvider


def test_chunking_engine_text():
    text = "Hello world. This is a text to chunk. It has some characters."
    # Chunk size 15, overlap 5
    chunks = ChunkingEngine.chunk_text(text, chunk_size=15, chunk_overlap=5)
    assert len(chunks) > 0
    for chunk, token_count in chunks:
        assert len(chunk) <= 15
        assert token_count == len(chunk.split())


def test_chunking_engine_item():
    item = KnowledgeItem(
        id=uuid4(),
        organization_id=uuid4(),
        project_id=uuid4(),
        source="github",
        source_entity_id="c1",
        entity_type="commit",
        title="Fix core layout bug",
        content="This is the content body of the layout bug. We fixed a centering issue.",
        description="Fix core layout bug",
        author="Alice",
        created_time=datetime.now(UTC),
        updated_time=datetime.now(UTC),
    )

    chunks = ChunkingEngine.chunk_item(item, chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 0
    assert chunks[0]["chunk_index"] == 0
    assert "content" in chunks[0]
    assert "token_count" in chunks[0]
    assert chunks[0]["metadata"]["source"] == "github"
    assert chunks[0]["metadata"]["entity_type"] == "commit"


@pytest.mark.asyncio
async def test_mock_embedding_provider():
    provider = MockEmbeddingProvider(dimensions=1536)
    texts = ["hello", "world", "hello"]

    embeddings = await provider.get_embeddings(texts)
    assert len(embeddings) == 3
    assert len(embeddings[0]) == 1536

    # Determinism check
    assert embeddings[0] == embeddings[2]
    assert embeddings[0] != embeddings[1]


@pytest.mark.asyncio
async def test_embedding_service_index():
    session = AsyncMock()
    service = EmbeddingService(session)

    item = KnowledgeItem(
        id=uuid4(),
        organization_id=uuid4(),
        project_id=uuid4(),
        source="notion",
        source_entity_id="page1",
        entity_type="notion_page",
        title="Welcome Page",
        content="Welcome to our project documentation! Here is the main outline.",
        author="Charlie",
        created_time=datetime.now(UTC),
        updated_time=datetime.now(UTC),
    )

    # Mock repository methods
    service.repo = MagicMock()
    service.repo.delete_chunks_by_item_id = AsyncMock()
    service.repo.create_chunk = AsyncMock(side_effect=lambda c: c)

    chunks = await service.index_knowledge_item(item, chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 0
    assert service.repo.delete_chunks_by_item_id.called
    assert service.repo.create_chunk.called
    assert len(chunks[0].embedding) == 1536


@pytest.mark.asyncio
async def test_embedding_queue_states():
    project_id = uuid4()
    state = EmbeddingQueueService.get_state(project_id)
    assert isinstance(state, ProjectQueueState)
    assert state.status == "idle"

    # Test pause on idle state does nothing/returns paused
    state = await EmbeddingQueueService.pause_indexing(project_id)
    assert state.status == "idle" or state.status == "paused"
