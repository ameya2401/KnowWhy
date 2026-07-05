import hashlib
import json
import logging
import time
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import create_redis_client
from app.models.knowledge import KnowledgeItem
from app.repositories.search import SearchRepository
from app.services.embeddings import EmbeddingService
from app.services.query_processor import QueryProcessor
from app.services.search_fusion import ReciprocalRankFusion, WeightedReRanker

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.search_repo = SearchRepository(db)
        self.embedding_service = EmbeddingService(db)

    async def search(
        self,
        project_id: UUID,
        user_id: UUID,
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
        """Search project knowledge and save query to user recent search history if q is present."""
        if q and q.strip():
            # Add to user recent search history in background/gracefully
            await self._add_recent_search(user_id, project_id, q.strip())

        return await self.search_repo.search(
            project_id=project_id,
            q=q,
            source=source,
            entity_type=entity_type,
            author=author,
            tags=tags,
            status=status,
            date_start=date_start,
            date_end=date_end,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )

    async def hybrid_search(
        self,
        project_id: UUID,
        user_id: UUID,
        q: str | None = None,
        source: str | None = None,
        entity_type: str | None = None,
        author: str | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
        date_start: datetime | None = None,
        date_end: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
        similarity_threshold: float = 0.3,
        top_k: int = 50,
        ranking_weights: dict | None = None,
    ) -> dict:
        """
        Search using both keyword and semantic methods, merge via RRF, and re-rank with custom weights.
        Supports caching and tracks performance analytics.
        """  # noqa: E501
        start_time = time.time()
        cache_key = None
        redis = None

        # 1. Cache Lookup
        if q and q.strip():
            params = {
                "project_id": str(project_id),
                "q": q.strip(),
                "source": source,
                "entity_type": entity_type,
                "author": author,
                "tags": tags,
                "status": status,
                "date_start": date_start.isoformat() if date_start else None,
                "date_end": date_end.isoformat() if date_end else None,
                "limit": limit,
                "offset": offset,
                "similarity_threshold": similarity_threshold,
                "top_k": top_k,
                "ranking_weights": ranking_weights,
            }
            params_str = json.dumps(params, sort_keys=True)
            h = hashlib.sha256(params_str.encode("utf-8")).hexdigest()
            cache_key = f"knowwhy:search_cache:{h}"

            try:
                redis = create_redis_client()
                cached_data = await redis.get(cache_key)
                if cached_data:
                    await redis.incr("knowwhy:search_analytics:cache_hits")
                    await redis.incr("knowwhy:search_analytics:query_count")

                    data = json.loads(cached_data)
                    latency_ms = (time.time() - start_time) * 1000.0
                    await redis.incrbyfloat("knowwhy:search_analytics:total_latency_ms", latency_ms)
                    await redis.close()
                    return data
            except Exception as e:
                logger.warning(f"Search cache lookup failed: {e}")

        # 2. Query Processing
        processed = QueryProcessor.process(q)
        q_clean = processed["normalized_query"] or q

        # 3. Retrieve Lexical Results
        lexical_results = []
        if q and q.strip():
            lex_res_tuples, _ = await self.search_repo.search(
                project_id=project_id,
                q=q_clean,
                source=source,
                entity_type=entity_type,
                author=author,
                tags=tags,
                status=status,
                date_start=date_start,
                date_end=date_end,
                sort_by="relevance",
                limit=top_k,
                offset=0,
            )
            lexical_results = lex_res_tuples

        # 4. Retrieve Semantic Results
        semantic_results = []
        if q and q.strip():
            try:
                query_embeddings = await self.embedding_service.provider.get_embeddings([q_clean])
                if query_embeddings:
                    query_embedding = query_embeddings[0]
                    semantic_results = await self.search_repo.semantic_search(
                        project_id=project_id,
                        query_embedding=query_embedding,
                        source=source,
                        entity_type=entity_type,
                        author=author,
                        status=status,
                        limit=top_k,
                        similarity_threshold=similarity_threshold,
                    )
            except Exception as e:
                logger.exception(f"Semantic search embedding retrieval failed: {e}")

        # 5. Fallback for empty query or no results from either
        if not lexical_results and not semantic_results:
            items_tuples, total = await self.search_repo.search(
                project_id=project_id,
                q=None,
                source=source,
                entity_type=entity_type,
                author=author,
                tags=tags,
                status=status,
                date_start=date_start,
                date_end=date_end,
                sort_by="recently_updated",
                limit=limit,
                offset=offset,
            )
            results = []
            for item, score in items_tuples:
                results.append(
                    {
                        "item": {
                            "id": str(item.id),
                            "organization_id": str(item.organization_id),
                            "project_id": str(item.project_id),
                            "source": item.source,
                            "source_entity_id": item.source_entity_id,
                            "entity_type": item.entity_type,
                            "title": item.title,
                            "description": item.description,
                            "content": item.content,
                            "url": item.url,
                            "author": item.author,
                            "created_time": item.created_time.isoformat(),
                            "updated_time": item.updated_time.isoformat(),
                            "tags": item.tags,
                            "status": item.status,
                        },
                        "score": score,
                        "confidence": 0.5,
                        "match_type": "lexical",
                        "explanation": {
                            "lexical_score": score,
                            "semantic_score": 0.0,
                            "rrf_score": 0.0,
                            "recency_score": 1.0,
                            "source_score": 0.5,
                            "matching_fields": ["title"],
                            "reasons": ["Default listing (recency ordered)"],
                        },
                    }
                )
            output = {"results": results, "total": total, "limit": limit, "offset": offset}
            if q and q.strip():
                await self._add_recent_search(user_id, project_id, q.strip())
            return output

        # 6. Apply Reciprocal Rank Fusion & Weighted Re-ranking
        fused = ReciprocalRankFusion().fuse(lexical_results, semantic_results)
        re_ranked = WeightedReRanker(ranking_weights).re_rank(fused)

        total = len(re_ranked)
        paginated = re_ranked[offset : offset + limit]

        results = []
        avg_similarity = 0.0
        similarity_count = 0

        for item, score, explain in paginated:
            lex_score = explain["lexical_score"]
            sem_score = explain["semantic_score"]
            match_type = "hybrid"
            if lex_score > 0 and sem_score == 0:
                match_type = "lexical"
            elif sem_score > 0 and lex_score == 0:
                match_type = "semantic"

            if sem_score > 0:
                avg_similarity += sem_score
                similarity_count += 1

            confidence = min(max(score, 0.0), 1.0)

            results.append(
                {
                    "item": {
                        "id": str(item.id),
                        "organization_id": str(item.organization_id),
                        "project_id": str(item.project_id),
                        "source": item.source,
                        "source_entity_id": item.source_entity_id,
                        "entity_type": item.entity_type,
                        "title": item.title,
                        "description": item.description,
                        "content": item.content,
                        "url": item.url,
                        "author": item.author,
                        "created_time": item.created_time.isoformat(),
                        "updated_time": item.updated_time.isoformat(),
                        "tags": item.tags,
                        "status": item.status,
                    },
                    "score": float(score),
                    "confidence": float(confidence),
                    "match_type": match_type,
                    "explanation": {
                        "lexical_score": float(lex_score),
                        "semantic_score": float(sem_score),
                        "rrf_score": float(explain["rrf_score"]),
                        "recency_score": float(explain["recency_score"]),
                        "source_score": float(explain["source_score"]),
                        "matching_fields": explain["matching_fields"],
                        "reasons": explain["reasons"],
                    },
                }
            )

        output = {"results": results, "total": total, "limit": limit, "offset": offset}

        # Save query to user search history
        if q and q.strip():
            await self._add_recent_search(user_id, project_id, q.strip())

        # 7. Analytics Tracking & Cache Write
        latency_ms = (time.time() - start_time) * 1000.0
        try:
            if not redis:
                redis = create_redis_client()
            await redis.incr("knowwhy:search_analytics:query_count")
            await redis.incr("knowwhy:search_analytics:cache_misses")
            await redis.incrbyfloat("knowwhy:search_analytics:total_latency_ms", latency_ms)
            if similarity_count > 0:
                await redis.incrbyfloat(
                    "knowwhy:search_analytics:total_similarity", avg_similarity / similarity_count
                )
                await redis.incr("knowwhy:search_analytics:similarity_count")

            if cache_key:
                await redis.setex(cache_key, 300, json.dumps(output))
            await redis.close()
        except Exception as e:
            logger.warning(f"Failed to track search analytics or cache results: {e}")

        return output

    async def get_search_statistics(self, project_id: UUID) -> dict:
        """Retrieve aggregated search performance metrics."""
        stats = await self.embedding_service.get_statistics(project_id)
        total_indexed = stats.get("indexed_documents", 0)

        query_count = 0
        cache_hits = 0
        total_latency = 0.0
        avg_similarity = 0.0

        try:
            redis = create_redis_client()
            q_count_str = await redis.get("knowwhy:search_analytics:query_count")
            c_hits_str = await redis.get("knowwhy:search_analytics:cache_hits")
            t_lat_str = await redis.get("knowwhy:search_analytics:total_latency_ms")
            t_sim_str = await redis.get("knowwhy:search_analytics:total_similarity")
            sim_cnt_str = await redis.get("knowwhy:search_analytics:similarity_count")
            await redis.close()

            if q_count_str:
                query_count = int(q_count_str)
            if c_hits_str:
                cache_hits = int(c_hits_str)
            if t_lat_str:
                total_latency = float(t_lat_str)
            if t_sim_str and sim_cnt_str:
                avg_similarity = float(t_sim_str) / max(int(sim_cnt_str), 1)
        except Exception:
            pass

        avg_query_time = (total_latency / max(query_count, 1)) if query_count > 0 else 0.0
        cache_hit_rate = (cache_hits / max(query_count, 1)) if query_count > 0 else 0.0

        return {
            "total_indexed_documents": total_indexed,
            "average_query_time_ms": avg_query_time,
            "cache_hit_rate": cache_hit_rate,
            "average_similarity_score": avg_similarity,
        }

    async def get_suggestions(self, project_id: UUID, q: str, limit: int = 10) -> list[str]:
        """Fetch matching query suggestions."""
        return await self.search_repo.get_suggestions(project_id, q, limit)

    async def get_available_filters(self, project_id: UUID) -> dict:
        """Fetch distinct filters present in the project knowledge store."""
        return await self.search_repo.get_available_filters(project_id)

    async def get_recent_searches(self, user_id: UUID, project_id: UUID) -> list[str]:
        """Retrieve recent search queries for a user and project context."""
        try:
            redis = create_redis_client()
            key = f"knowwhy:recent_searches:{str(user_id)}:{str(project_id)}"
            searches = await redis.lrange(key, 0, 9)
            await redis.close()
            return searches
        except Exception:
            return []

    async def _add_recent_search(self, user_id: UUID, project_id: UUID, query: str) -> None:
        """Track user query in Redis list."""
        try:
            redis = create_redis_client()
            key = f"knowwhy:recent_searches:{str(user_id)}:{str(project_id)}"
            await redis.lrem(key, 0, query)
            await redis.lpush(key, query)
            await redis.ltrim(key, 0, 9)
            await redis.expire(key, 30 * 24 * 3600)
            await redis.close()
        except Exception:
            pass
