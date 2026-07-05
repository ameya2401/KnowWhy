import { apiClient } from "@/services/apiClient";
import type {
  AvailableFilters,
  RecentSearchesResponse,
  SearchResponse,
  SuggestionsResponse,
  HybridSearchResponse,
  SearchStatisticsResponse,
} from "@/types/search";

export async function searchKnowledge(
  accessToken: string,
  projectId: string,
  params: {
    q?: string;
    source?: string;
    entity_type?: string;
    author?: string;
    tags?: string; // comma-separated
    status?: string;
    date_start?: string;
    date_end?: string;
    sort_by?: string;
    limit?: number;
    offset?: number;
  } = {},
): Promise<SearchResponse> {
  const response = await apiClient.get<SearchResponse>("/search", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId, ...params },
  });
  return response.data;
}

export async function getSearchSuggestions(
  accessToken: string,
  projectId: string,
  q: string,
  limit = 10,
): Promise<SuggestionsResponse> {
  const response = await apiClient.get<SuggestionsResponse>("/search/suggestions", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId, q, limit },
  });
  return response.data;
}

export async function getRecentSearches(
  accessToken: string,
  projectId: string,
): Promise<RecentSearchesResponse> {
  const response = await apiClient.get<RecentSearchesResponse>("/search/recent", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}

export async function getAvailableFilters(
  accessToken: string,
  projectId: string,
): Promise<AvailableFilters> {
  const response = await apiClient.get<AvailableFilters>("/search/filters", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}

export async function searchHybridKnowledge(
  accessToken: string,
  projectId: string,
  params: {
    q?: string;
    source?: string;
    entity_type?: string;
    author?: string;
    tags?: string;
    status?: string;
    date_start?: string;
    date_end?: string;
    similarity_threshold?: number;
    top_k?: number;
    limit?: number;
    offset?: number;
  } = {},
): Promise<HybridSearchResponse> {
  const response = await apiClient.get<HybridSearchResponse>("/search/hybrid", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId, ...params },
  });
  return response.data;
}

export async function getSearchStatistics(
  accessToken: string,
  projectId: string,
): Promise<SearchStatisticsResponse> {
  const response = await apiClient.get<SearchStatisticsResponse>("/search/statistics", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}

export async function triggerSearchReindex(
  accessToken: string,
  projectId: string,
): Promise<{ status: string }> {
  const response = await apiClient.post<{ status: string }>("/search/reindex", null, {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}
