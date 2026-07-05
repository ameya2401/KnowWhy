from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.knowledge import require_project_membership
from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.search import (
    AvailableFiltersResponse,
    HybridSearchResponse,
    RecentSearchesResponse,
    SearchExplanation,
    SearchResponse,
    SearchResultRead,
    SearchStatisticsResponse,
    SuggestionsResponse,
)
from app.services.search import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def perform_search(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
    q: str | None = None,
    source: str | None = None,
    entity_type: str | None = None,
    author: str | None = None,
    tags: str | None = None,
    status: str | None = None,
    date_start: datetime | None = None,
    date_end: datetime | None = None,
    sort_by: str = "relevance",
    limit: int = 20,
    offset: int = 0,
):
    """Perform keyword and metadata search across all normalized project resources."""
    await require_project_membership(current_user, project_id, db)
    service = SearchService(db)

    # Process comma-separated tags filter
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    results, total = await service.search(
        project_id=project_id,
        user_id=current_user.id,
        q=q,
        source=source,
        entity_type=entity_type,
        author=author,
        tags=tag_list,
        status=status,
        date_start=date_start,
        date_end=date_end,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )

    # Map raw rows (item, score) to response schema
    formatted_results = [SearchResultRead(item=item, score=score) for item, score in results]

    return SearchResponse(
        results=formatted_results,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/hybrid", response_model=HybridSearchResponse)
async def perform_hybrid_search(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
    q: str | None = None,
    source: str | None = None,
    entity_type: str | None = None,
    author: str | None = None,
    tags: str | None = None,
    status: str | None = None,
    date_start: datetime | None = None,
    date_end: datetime | None = None,
    similarity_threshold: float = 0.3,
    top_k: int = 50,
    limit: int = 20,
    offset: int = 0,
):
    """Retrieve search results fusing keyword (lexical) and embeddings (semantic) methods."""
    await require_project_membership(current_user, project_id, db)
    service = SearchService(db)

    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    output = await service.hybrid_search(
        project_id=project_id,
        user_id=current_user.id,
        q=q,
        source=source,
        entity_type=entity_type,
        author=author,
        tags=tag_list,
        status=status,
        date_start=date_start,
        date_end=date_end,
        similarity_threshold=similarity_threshold,
        top_k=top_k,
        limit=limit,
        offset=offset,
    )
    return HybridSearchResponse(**output)


@router.get("/explain/{item_id}", response_model=SearchExplanation)
async def get_search_explanation(
    item_id: UUID,
    project_id: UUID,
    q: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Explain why a specific knowledge item matched a query, returning lexical/semantic breakdown."""  # noqa: E501
    await require_project_membership(current_user, project_id, db)
    service = SearchService(db)

    # Perform hybrid search with a broader scope to find the item
    search_data = await service.hybrid_search(
        project_id=project_id,
        user_id=current_user.id,
        q=q,
        limit=100,
        offset=0,
    )

    for idx, res in enumerate(search_data["results"]):
        if res["item"]["id"] == str(item_id):
            exp = res["explanation"]
            return SearchExplanation(
                lexical_score=exp["lexical_score"],
                semantic_score=exp["semantic_score"],
                final_rank=idx + 1,
                matching_fields=exp["matching_fields"],
                reasons=exp["reasons"],
            )

    return SearchExplanation(
        lexical_score=0.0,
        semantic_score=0.0,
        final_rank=-1,
        matching_fields=[],
        reasons=["Item was not retrieved in top search results."],
    )


@router.get("/statistics", response_model=SearchStatisticsResponse)
async def get_search_statistics(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Retrieve query performance statistics and embedding indexing status."""
    await require_project_membership(current_user, project_id, db)
    service = SearchService(db)
    stats = await service.get_search_statistics(project_id)
    return SearchStatisticsResponse(**stats)


@router.post("/reindex")
async def trigger_search_reindex(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Trigger background re-indexing of all documents for this project."""
    await require_project_membership(current_user, project_id, db)
    from app.services.embedding_queue import EmbeddingQueueService

    await EmbeddingQueueService.reindex_project(project_id)
    return {"status": "reindexing_started"}


@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_search_suggestions(
    project_id: UUID,
    q: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
    limit: int = 10,
):
    """Retrieve distinct search keyword suggestions matching a partial query."""
    await require_project_membership(current_user, project_id, db)
    service = SearchService(db)
    suggestions = await service.get_suggestions(project_id, q, limit)
    return SuggestionsResponse(suggestions=suggestions)


@router.get("/recent", response_model=RecentSearchesResponse)
async def get_recent_searches(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Retrieve recent queries searched by the current user within this project."""
    await require_project_membership(current_user, project_id, db)
    service = SearchService(db)
    queries = await service.get_recent_searches(current_user.id, project_id)
    return RecentSearchesResponse(queries=queries)


@router.get("/filters", response_model=AvailableFiltersResponse)
async def get_available_filters(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Fetch all distinct sources, entity types, authors, and tags currently present."""
    await require_project_membership(current_user, project_id, db)
    service = SearchService(db)
    filters = await service.get_available_filters(project_id)
    return AvailableFiltersResponse(
        sources=filters["sources"],
        entity_types=filters["entity_types"],
        authors=filters["authors"],
        tags=filters["tags"],
    )
