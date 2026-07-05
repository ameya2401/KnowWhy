import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select

from app.database.session import async_session_factory
from app.models.knowledge import KnowledgeChunk, KnowledgeItem
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class ProjectQueueState:
    def __init__(self, project_id: UUID) -> None:
        self.project_id = project_id
        self.status: str = "idle"  # "idle", "running", "paused", "completed", "failed"
        self.total_items: int = 0
        self.processed_items: int = 0
        self.failed_items: int = 0
        self.last_index_time: str | None = None
        self.error_message: str | None = None
        self.pending_item_ids: list[UUID] = []
        self.failed_item_ids: list[UUID] = []


class EmbeddingQueueService:
    _states: dict[UUID, ProjectQueueState] = {}
    _tasks: dict[UUID, asyncio.Task] = {}

    @classmethod
    def get_state(cls, project_id: UUID) -> ProjectQueueState:
        if project_id not in cls._states:
            cls._states[project_id] = ProjectQueueState(project_id)
        return cls._states[project_id]

    @classmethod
    async def start_indexing(cls, project_id: UUID) -> ProjectQueueState:
        state = cls.get_state(project_id)

        if state.status == "running":
            return state

        # Get all active knowledge items that need to be indexed
        async with async_session_factory() as session:
            stmt = select(KnowledgeItem.id).where(
                KnowledgeItem.project_id == project_id, KnowledgeItem.status == "active"
            )
            res = await session.execute(stmt)
            item_ids = list(res.scalars().all())

        state.status = "running"
        state.total_items = len(item_ids)
        state.processed_items = 0
        state.failed_items = 0
        state.pending_item_ids = item_ids
        state.failed_item_ids = []
        state.error_message = None

        # Start background worker task
        cls._tasks[project_id] = asyncio.create_task(cls._worker(project_id))
        return state

    @classmethod
    async def pause_indexing(cls, project_id: UUID) -> ProjectQueueState:
        state = cls.get_state(project_id)
        if state.status == "running":
            state.status = "paused"
            if project_id in cls._tasks:
                cls._tasks[project_id].cancel()
        return state

    @classmethod
    async def resume_indexing(cls, project_id: UUID) -> ProjectQueueState:
        state = cls.get_state(project_id)
        if state.status == "paused":
            state.status = "running"
            cls._tasks[project_id] = asyncio.create_task(cls._worker(project_id))
        return state

    @classmethod
    async def reindex_project(cls, project_id: UUID) -> ProjectQueueState:
        state = cls.get_state(project_id)

        # Cancel active indexing if running
        if state.status == "running" and project_id in cls._tasks:
            state.status = "paused"
            cls._tasks[project_id].cancel()

        # Delete all existing chunks first
        async with async_session_factory() as session:
            # Delete chunks whose knowledge items belong to this project
            item_stmt = select(KnowledgeItem.id).where(KnowledgeItem.project_id == project_id)
            res = await session.execute(item_stmt)
            item_ids = list(res.scalars().all())

            if item_ids:
                del_stmt = delete(KnowledgeChunk).where(
                    KnowledgeChunk.knowledge_item_id.in_(item_ids)
                )
                await session.execute(del_stmt)
                await session.commit()

        # Re-initialize indexing
        state.status = "running"
        state.total_items = len(item_ids)
        state.processed_items = 0
        state.failed_items = 0
        state.pending_item_ids = item_ids
        state.failed_item_ids = []
        state.error_message = None

        cls._tasks[project_id] = asyncio.create_task(cls._worker(project_id))
        return state

    @classmethod
    async def _worker(cls, project_id: UUID) -> None:
        state = cls.get_state(project_id)
        try:
            while state.pending_item_ids and state.status == "running":
                item_id = state.pending_item_ids.pop(0)

                # Process this item with a retry loop
                retries = 3
                success = False
                while retries > 0:
                    try:
                        async with async_session_factory() as session:
                            item_stmt = select(KnowledgeItem).where(KnowledgeItem.id == item_id)
                            item_res = await session.execute(item_stmt)
                            item = item_res.scalar_one_or_none()

                            if item:
                                embed_service = EmbeddingService(session)
                                await embed_service.index_knowledge_item(item)

                            success = True
                            break
                    except asyncio.CancelledError:
                        # Put back item if cancelled
                        state.pending_item_ids.insert(0, item_id)
                        raise
                    except Exception as e:
                        retries -= 1
                        logger.warning(
                            f"Failed to index item {item_id}, retries left={retries}: {e}"
                        )
                        await asyncio.sleep(0.5)

                if success:
                    state.processed_items += 1
                else:
                    state.failed_items += 1
                    state.failed_item_ids.append(item_id)

            if state.status == "running":
                state.status = "completed"
                state.last_index_time = datetime.now(UTC).isoformat()

        except asyncio.CancelledError:
            # Task cancelled via pause/cancel
            logger.info(f"Indexing worker for project {project_id} paused/cancelled.")
        except Exception as e:
            logger.exception(f"Unhandled exception in indexing worker for project {project_id}")
            state.status = "failed"
            state.error_message = str(e)
            state.last_index_time = datetime.now(UTC).isoformat()
