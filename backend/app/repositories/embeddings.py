from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk, KnowledgeItem


class EmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_chunk(self, chunk: KnowledgeChunk) -> KnowledgeChunk:
        self.session.add(chunk)
        await self.session.flush()
        return chunk

    async def delete_chunks_by_item_id(self, knowledge_item_id: UUID) -> None:
        await self.session.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.knowledge_item_id == knowledge_item_id)
        )
        await self.session.flush()

    async def get_chunks_by_item_id(self, knowledge_item_id: UUID) -> list[KnowledgeChunk]:
        result = await self.session.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.knowledge_item_id == knowledge_item_id)
            .order_by(KnowledgeChunk.chunk_index.asc())
        )
        return list(result.scalars().all())

    async def get_total_chunks(self, project_id: UUID | None = None) -> int:
        stmt = select(func.count(KnowledgeChunk.id))
        if project_id:
            stmt = stmt.join(KnowledgeItem).where(KnowledgeItem.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_total_indexed_documents(self, project_id: UUID | None = None) -> int:
        # Number of unique knowledge items that have chunks
        stmt = select(func.count(func.distinct(KnowledgeChunk.knowledge_item_id)))
        if project_id:
            stmt = stmt.join(KnowledgeItem).where(KnowledgeItem.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()
