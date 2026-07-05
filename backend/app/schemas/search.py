from pydantic import BaseModel

from app.schemas.knowledge import KnowledgeItemRead


class SearchResultRead(BaseModel):
    item: KnowledgeItemRead
    score: float

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    results: list[SearchResultRead]
    total: int
    limit: int
    offset: int


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


class RecentSearchesResponse(BaseModel):
    queries: list[str]


class AvailableFiltersResponse(BaseModel):
    sources: list[str]
    entity_types: list[str]
    authors: list[str]
    tags: list[str]


class SearchExplanation(BaseModel):
    lexical_score: float
    semantic_score: float
    final_rank: int
    matching_fields: list[str]
    reasons: list[str]


class HybridSearchResult(BaseModel):
    item: KnowledgeItemRead
    score: float
    confidence: float
    match_type: str  # "lexical", "semantic", "hybrid"
    explanation: SearchExplanation


class HybridSearchResponse(BaseModel):
    results: list[HybridSearchResult]
    total: int
    limit: int
    offset: int


class SearchStatisticsResponse(BaseModel):
    total_indexed_documents: int
    average_query_time_ms: float
    cache_hit_rate: float
    average_similarity_score: float
