import type { KnowledgeItem } from "./knowledge";

export interface SearchResult {
  item: KnowledgeItem;
  score: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  limit: number;
  offset: number;
}

export interface SuggestionsResponse {
  suggestions: string[];
}

export interface RecentSearchesResponse {
  queries: string[];
}

export interface AvailableFilters {
  sources: string[];
  entity_types: string[];
  authors: string[];
  tags: string[];
}

export interface SearchExplanation {
  lexical_score: number;
  semantic_score: number;
  final_rank: number;
  matching_fields: string[];
  reasons: string[];
}

export interface HybridSearchResult {
  item: KnowledgeItem;
  score: number;
  confidence: number;
  match_type: "lexical" | "semantic" | "hybrid";
  explanation: SearchExplanation;
}

export interface HybridSearchResponse {
  results: HybridSearchResult[];
  total: number;
  limit: number;
  offset: number;
}

export interface SearchStatisticsResponse {
  total_indexed_documents: number;
  average_query_time_ms: number;
  cache_hit_rate: number;
  average_similarity_score: number;
}

