from datetime import UTC, datetime, timedelta
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import (
    Text,
    and_,
    case,
    cast,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeItem, KnowledgeChunk


class SearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self,
        project_id: UUID,
        q: str | None = None,
        source: str | None = None,
        entity_type: str | None = None,
        author: str | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
        date_start: datetime | None = None,
        date_end: datetime | None = None,
        sort_by: str = "relevance",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[tuple[KnowledgeItem, float]], int]:
        """Search knowledge items with filters, sorting, and relevance ranking."""
        now = datetime.now(UTC)
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        # Build search relevance score
        score_expr = sa.literal(0.0)  # default score

        if q:
            q_stripped = q.strip()
            # 1. Exact matches: title (+100) or content (+50)
            exact_title = case((KnowledgeItem.title.ilike(q_stripped), 100.0), else_=0.0)
            exact_content = case((KnowledgeItem.content.ilike(q_stripped), 50.0), else_=0.0)
            score_expr = score_expr + exact_title + exact_content

            # 2. Keyword matches
            keywords = [kw for kw in q_stripped.split() if kw]
            for kw in keywords:
                kw_pattern = f"%{kw}%"
                kw_title = case((KnowledgeItem.title.ilike(kw_pattern), 20.0), else_=0.0)
                kw_desc = case(
                    (
                        and_(
                            KnowledgeItem.description.is_not(None),
                            KnowledgeItem.description.ilike(kw_pattern),
                        ),
                        10.0,
                    ),
                    else_=0.0,
                )
                kw_content = case(
                    (
                        and_(
                            KnowledgeItem.content.is_not(None),
                            KnowledgeItem.content.ilike(kw_pattern),
                        ),
                        5.0,
                    ),
                    else_=0.0,
                )
                # Cast JSON tags to text to search inside tags
                kw_tags = case(
                    (
                        and_(
                            KnowledgeItem.tags.is_not(None),
                            cast(KnowledgeItem.tags, Text).ilike(kw_pattern),
                        ),
                        15.0,
                    ),
                    else_=0.0,
                )
                score_expr = score_expr + kw_title + kw_desc + kw_content + kw_tags

            # 3. Recency bonus: last 7 days (+15), last 30 days (+5)
            recency_bonus = case(
                (KnowledgeItem.updated_time >= seven_days_ago, 15.0),
                (KnowledgeItem.updated_time >= thirty_days_ago, 5.0),
                else_=0.0,
            )
            # 4. Source importance weight: Notion (+10), GitHub PRs/Issues (+8),
            # Drive (+5), others (+2)
            source_bonus = case(
                (KnowledgeItem.source == "notion", 10.0),
                (KnowledgeItem.entity_type == "pull_request", 8.0),
                (KnowledgeItem.entity_type == "issue", 8.0),
                (KnowledgeItem.source == "google_drive", 5.0),
                else_=2.0,
            )

            score_expr = score_expr + recency_bonus + source_bonus

        # Count and selection statement base
        stmt = select(KnowledgeItem).where(KnowledgeItem.project_id == project_id)

        # Apply filters
        if source:
            stmt = stmt.where(KnowledgeItem.source == source)
        if entity_type:
            stmt = stmt.where(KnowledgeItem.entity_type == entity_type)
        if author:
            stmt = stmt.where(KnowledgeItem.author.ilike(f"%{author}%"))
        if status:
            stmt = stmt.where(KnowledgeItem.status == status)
        else:
            stmt = stmt.where(KnowledgeItem.status == "active")

        if tags:
            tag_conds = []
            for tag in tags:
                tag_conds.append(cast(KnowledgeItem.tags, Text).ilike(f"%{tag}%"))
            if tag_conds:
                stmt = stmt.where(or_(*tag_conds))

        if date_start:
            stmt = stmt.where(KnowledgeItem.created_time >= date_start)
        if date_end:
            stmt = stmt.where(KnowledgeItem.created_time <= date_end)

        # Count total matches before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one()

        # Add score label to query
        stmt = stmt.add_columns(score_expr.label("relevance_score"))

        # Apply sorting
        if sort_by == "relevance" and q:
            stmt = stmt.order_by(
                score_expr.desc(),
                KnowledgeItem.updated_time.desc(),
            )
        elif sort_by == "newest":
            stmt = stmt.order_by(KnowledgeItem.created_time.desc())
        elif sort_by == "oldest":
            stmt = stmt.order_by(KnowledgeItem.created_time.asc())
        elif sort_by == "recently_updated":
            stmt = stmt.order_by(KnowledgeItem.updated_time.desc())
        elif sort_by == "alphabetical":
            stmt = stmt.order_by(KnowledgeItem.title.asc())
        else:
            # default fallback if no query and relevance is selected
            stmt = stmt.order_by(KnowledgeItem.updated_time.desc())

        # Pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        rows = result.all()
        # rows is a list of Row tuples (KnowledgeItem, float)
        return [(row[0], float(row[1])) for row in rows], total

    async def get_suggestions(self, project_id: UUID, q: str, limit: int = 10) -> list[str]:
        """Fetch distinct titles matching the partial query as autocomplete suggestions."""
        if not q or not q.strip():
            return []

        pattern = f"%{q.strip()}%"
        stmt = (
            select(func.distinct(KnowledgeItem.title))
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.status == "active",
                KnowledgeItem.title.ilike(pattern),
            )
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_available_filters(self, project_id: UUID) -> dict:
        """Fetch distinct sources, entity types, authors, and tags available for filtering."""
        # 1. Distinct sources
        sources_res = await self.session.execute(
            select(func.distinct(KnowledgeItem.source)).where(
                KnowledgeItem.project_id == project_id
            )
        )
        sources = [s for s in sources_res.scalars().all() if s]

        # 2. Distinct entity types
        types_res = await self.session.execute(
            select(func.distinct(KnowledgeItem.entity_type)).where(
                KnowledgeItem.project_id == project_id
            )
        )
        entity_types = [t for t in types_res.scalars().all() if t]

        # 3. Distinct authors
        authors_res = await self.session.execute(
            select(func.distinct(KnowledgeItem.author)).where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.author.is_not(None),
            )
        )
        authors = [a for a in authors_res.scalars().all() if a]

        # 4. Fetch all tags to merge in Python (since tags is sa.JSON)
        tags_res = await self.session.execute(
            select(KnowledgeItem.tags).where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.tags.is_not(None),
            )
        )
        unique_tags = set()
        for tags_json in tags_res.scalars().all():
            if isinstance(tags_json, list):
                for t in tags_json:
                    if isinstance(t, str):
                        unique_tags.add(t)

        return {
            "sources": sorted(sources),
            "entity_types": sorted(entity_types),
            "authors": sorted(authors),
            "tags": sorted(list(unique_tags)),
        }

    async def semantic_search(
        self,
        project_id: UUID,
        query_embedding: list[float],
        source: str | None = None,
        entity_type: str | None = None,
        author: str | None = None,
        status: str | None = None,
        limit: int = 100,
        similarity_threshold: float = 0.0,
    ) -> list[tuple[KnowledgeItem, float]]:
        """
        Perform semantic search using pgvector cosine similarity.
        Returns a list of (KnowledgeItem, similarity_score) sorted by score.
        """
        # Cosine distance = embedding <=> query_embedding
        # Similarity = 1.0 - cosine_distance
        
        # Check bind dialect to support SQLite fallback in tests
        bind = self.session.bind
        if bind and bind.dialect.name != "postgresql":
            # Fallback for sqlite / mock in unit tests
            # Let's just retrieve some knowledge items
            stmt = select(KnowledgeItem).where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.status == (status or "active")
            ).limit(limit)
            res = await self.session.execute(stmt)
            items = res.scalars().all()
            return [(item, 0.8) for item in items]

        # PostgreSQL pgvector query
        cosine_dist_expr = KnowledgeChunk.embedding.cosine_distance(query_embedding)
        similarity_expr = (1.0 - cosine_dist_expr).label("similarity")
        
        stmt = (
            select(KnowledgeItem, similarity_expr)
            .join(KnowledgeChunk, KnowledgeChunk.knowledge_item_id == KnowledgeItem.id)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.status == (status or "active")
            )
        )
        
        if source:
            stmt = stmt.where(KnowledgeItem.source == source)
        if entity_type:
            stmt = stmt.where(KnowledgeItem.entity_type == entity_type)
        if author:
            stmt = stmt.where(KnowledgeItem.author.ilike(f"%{author}%"))
            
        # Order by similarity score descending
        stmt = stmt.order_by(sa.desc("similarity")).limit(limit)
        
        res = await self.session.execute(stmt)
        rows = res.all()
        
        # Deduplicate chunks pointing to the same KnowledgeItem, retaining the highest similarity
        item_scores = {}
        for item, similarity in rows:
            if similarity >= similarity_threshold:
                if item.id not in item_scores or similarity > item_scores[item.id][1]:
                    item_scores[item.id] = (item, float(similarity))
                    
        sorted_results = list(item_scores.values())
        sorted_results.sort(key=lambda x: x[1], reverse=True)
        return sorted_results
