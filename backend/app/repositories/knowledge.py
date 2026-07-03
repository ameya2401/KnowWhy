from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.knowledge import KnowledgeItem, KnowledgeRelationship, KnowledgeSyncLog


class KnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_item(self, item: KnowledgeItem) -> KnowledgeItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_item_by_id(self, item_id: UUID) -> KnowledgeItem | None:
        result = await self.session.execute(
            select(KnowledgeItem)
            .options(
                selectinload(KnowledgeItem.outgoing_relationships).selectinload(
                    KnowledgeRelationship.target_item
                ),
                selectinload(KnowledgeItem.incoming_relationships).selectinload(
                    KnowledgeRelationship.source_item
                ),
            )
            .where(KnowledgeItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_item_by_source_id(
        self, project_id: UUID, source: str, source_entity_id: str
    ) -> KnowledgeItem | None:
        result = await self.session.execute(
            select(KnowledgeItem).where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.source == source,
                KnowledgeItem.source_entity_id == source_entity_id,
            )
        )
        return result.scalar_one_or_none()

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
        # Build count query
        count_stmt = select(func.count(KnowledgeItem.id)).where(
            KnowledgeItem.project_id == project_id
        )
        # Build items query
        items_stmt = select(KnowledgeItem).where(KnowledgeItem.project_id == project_id)

        if source:
            count_stmt = count_stmt.where(KnowledgeItem.source == source)
            items_stmt = items_stmt.where(KnowledgeItem.source == source)
        if entity_type:
            count_stmt = count_stmt.where(KnowledgeItem.entity_type == entity_type)
            items_stmt = items_stmt.where(KnowledgeItem.entity_type == entity_type)
        if status:
            count_stmt = count_stmt.where(KnowledgeItem.status == status)
            items_stmt = items_stmt.where(KnowledgeItem.status == status)
        if search:
            search_filter = or_(
                KnowledgeItem.title.ilike(f"%{search}%"),
                KnowledgeItem.description.ilike(f"%{search}%"),
                KnowledgeItem.content.ilike(f"%{search}%"),
            )
            count_stmt = count_stmt.where(search_filter)
            items_stmt = items_stmt.where(search_filter)

        # Count execution
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Items execution
        items_stmt = (
            items_stmt.order_by(KnowledgeItem.updated_time.desc()).limit(limit).offset(offset)
        )
        items_result = await self.session.execute(items_stmt)
        items = list(items_result.scalars().all())

        return items, total

    async def create_relationship(
        self, relationship: KnowledgeRelationship
    ) -> KnowledgeRelationship:
        self.session.add(relationship)
        await self.session.flush()
        return relationship

    async def get_relationship(
        self, source_item_id: UUID, target_item_id: UUID, relationship_type: str
    ) -> KnowledgeRelationship | None:
        result = await self.session.execute(
            select(KnowledgeRelationship).where(
                KnowledgeRelationship.source_item_id == source_item_id,
                KnowledgeRelationship.target_item_id == target_item_id,
                KnowledgeRelationship.relationship_type == relationship_type,
            )
        )
        return result.scalar_one_or_none()

    async def list_relationships(self, item_id: UUID) -> list[KnowledgeRelationship]:
        result = await self.session.execute(
            select(KnowledgeRelationship)
            .options(
                selectinload(KnowledgeRelationship.source_item),
                selectinload(KnowledgeRelationship.target_item),
            )
            .where(
                or_(
                    KnowledgeRelationship.source_item_id == item_id,
                    KnowledgeRelationship.target_item_id == item_id,
                )
            )
        )
        return list(result.scalars().all())

    async def create_sync_log(self, log: KnowledgeSyncLog) -> KnowledgeSyncLog:
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_sync_log_by_id(self, log_id: UUID) -> KnowledgeSyncLog | None:
        result = await self.session.execute(
            select(KnowledgeSyncLog).where(KnowledgeSyncLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_sync_log(self, project_id: UUID) -> KnowledgeSyncLog | None:
        result = await self.session.execute(
            select(KnowledgeSyncLog)
            .where(KnowledgeSyncLog.project_id == project_id)
            .order_by(KnowledgeSyncLog.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_timeline(
        self,
        project_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeItem]:
        # Timeline retrieves items ordered chronologically by updated_time
        result = await self.session.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.status == "active",
            )
            .order_by(KnowledgeItem.updated_time.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
