import abc
import hashlib
import logging
import random
from uuid import UUID, uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.knowledge import KnowledgeChunk, KnowledgeItem
from app.repositories.embeddings import EmbeddingRepository

logger = logging.getLogger(__name__)


class ChunkingEngine:
    """Intelligent text chunking engine supporting configurable sizes and overlaps."""

    @staticmethod
    def calculate_tokens(text: str) -> int:
        """Approximates the token count based on words."""
        if not text:
            return 0
        return len(text.split())

    @classmethod
    def chunk_text(
        cls, text: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> list[tuple[str, int]]:
        """Splits text into chunks of maximum character length chunk_size with overlap."""
        if not text:
            return []

        # List of (chunk_content, token_count)
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_content = text[start:end]
            token_count = cls.calculate_tokens(chunk_content)
            chunks.append((chunk_content, token_count))

            # Move start pointer forward
            if end == text_len:
                break
            start += chunk_size - chunk_overlap
            # Prevent infinite loops if overlap is misconfigured
            if start >= end:
                start = end

        return chunks

    @classmethod
    def chunk_item(
        cls, item: KnowledgeItem, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> list[dict]:
        """Constructs formatted text payload for knowledge item and chunks it."""
        # Custom formatting based on source/type to inject metadata context
        header = f"Source: {item.source} | Type: {item.entity_type} | Title: {item.title}\n"
        if item.author:
            header += f"Author: {item.author}\n"

        content_body = ""
        if item.content:
            content_body += item.content
        if item.description and item.description != item.content:
            content_body += f"\nDescription: {item.description}"

        full_text = header + "\n" + content_body
        text_chunks = cls.chunk_text(full_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        chunks_data = []
        for index, (chunk_content, tokens) in enumerate(text_chunks):
            chunks_data.append(
                {
                    "chunk_index": index,
                    "content": chunk_content,
                    "token_count": tokens,
                    "metadata": {
                        "original_item_id": str(item.id),
                        "source": item.source,
                        "entity_type": item.entity_type,
                        "title": item.title,
                        "url": item.url,
                    },
                }
            )
        return chunks_data


class EmbeddingProvider(abc.ABC):
    """Abstract Base Class for Interchangeable Embedding Providers."""

    @abc.abstractmethod
    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generates embedding vectors for a list of texts."""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    """Generates deterministic pseudo-random vectors for testing and development."""

    def __init__(self, dimensions: int = 1536) -> None:
        self.dimensions = dimensions

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            # Deterministic seed using SHA256 of text
            h = hashlib.sha256(text.encode("utf-8")).digest()
            # Seed python's PRNG locally for this vector
            random_state = random.getstate()
            random.seed(int.from_bytes(h[:8], byteorder="big"))
            vec = [random.gauss(0, 1) for _ in range(self.dimensions)]
            # Normalize vector
            norm = sum(x * x for x in vec) ** 0.5
            normalized_vec = [x / norm for x in vec] if norm > 0 else [0.0] * self.dimensions
            results.append(normalized_vec)
            # Restore state
            random.setstate(random_state)
        return results


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Generates embedding vectors using OpenAI's API."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        self.api_key = api_key
        self.model = model
        self.mock_provider = MockEmbeddingProvider()

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            # Fallback to mock provider if no API key is configured
            return await self.mock_provider.get_embeddings(texts)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"input": texts, "model": self.model},
                )
                if response.status_code == 200:
                    data = response.json()
                    return [item["embedding"] for item in data["data"]]
                else:
                    logger.warning(
                        "OpenAI Embedding API failed (HTTP %s): %s",
                        response.status_code,
                        response.text,
                    )
                    # Fallback to mock on error to maintain system resilience
                    return await self.mock_provider.get_embeddings(texts)
        except Exception as e:
            logger.exception(f"Exception during OpenAI Embedding call: {e}")
            return await self.mock_provider.get_embeddings(texts)


def get_embedding_provider() -> EmbeddingProvider:
    """Factory helper returning provider based on config."""
    if settings.environment == "testing":
        return MockEmbeddingProvider()

    if settings.embedding_provider == "openai":
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key, model=settings.embedding_model
        )

    # Fallback default
    return MockEmbeddingProvider()


class EmbeddingService:
    """Coordinates embedding generation, chunking, and db persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = EmbeddingRepository(session)
        self.provider = get_embedding_provider()

    async def index_knowledge_item(
        self, item: KnowledgeItem, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> list[KnowledgeChunk]:
        """Chunks content, generates embeddings, and saves to knowledge_chunks database."""
        # 1. Delete existing chunks for item
        await self.repo.delete_chunks_by_item_id(item.id)

        # 2. Get chunks data
        chunks_data = ChunkingEngine.chunk_item(
            item, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        if not chunks_data:
            return []

        # 3. Generate embeddings in batch
        texts = [c["content"] for c in chunks_data]
        embeddings = await self.provider.get_embeddings(texts)

        # 4. Save chunks with embeddings
        saved_chunks = []
        for i, chunk_dict in enumerate(chunks_data):
            chunk = KnowledgeChunk(
                id=uuid4(),
                knowledge_item_id=item.id,
                chunk_index=chunk_dict["chunk_index"],
                content=chunk_dict["content"],
                token_count=chunk_dict["token_count"],
                embedding=embeddings[i],
                metadata_json=chunk_dict["metadata"],
                source=item.source,
            )
            saved_chunk = await self.repo.create_chunk(chunk)
            saved_chunks.append(saved_chunk)

        await self.session.commit()
        return saved_chunks

    async def get_statistics(self, project_id: UUID) -> dict:
        total_chunks = await self.repo.get_total_chunks(project_id)
        indexed_docs = await self.repo.get_total_indexed_documents(project_id)
        return {
            "total_chunks": total_chunks,
            "indexed_documents": indexed_docs,
        }
