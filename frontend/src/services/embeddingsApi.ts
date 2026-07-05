import { apiClient } from "@/services/apiClient";
import type { EmbeddingQueueStatus, EmbeddingStatistics } from "@/types/embeddings";

export async function startIndexing(
  accessToken: string,
  projectId: string,
): Promise<EmbeddingQueueStatus> {
  const response = await apiClient.post<EmbeddingQueueStatus>(
    "/embeddings/index",
    { project_id: projectId },
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  return response.data;
}

export async function pauseIndexing(
  accessToken: string,
  projectId: string,
): Promise<EmbeddingQueueStatus> {
  const response = await apiClient.post<EmbeddingQueueStatus>(
    "/embeddings/pause",
    { project_id: projectId },
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  return response.data;
}

export async function resumeIndexing(
  accessToken: string,
  projectId: string,
): Promise<EmbeddingQueueStatus> {
  const response = await apiClient.post<EmbeddingQueueStatus>(
    "/embeddings/resume",
    { project_id: projectId },
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  return response.data;
}

export async function reindexProject(
  accessToken: string,
  projectId: string,
): Promise<EmbeddingQueueStatus> {
  const response = await apiClient.post<EmbeddingQueueStatus>(
    "/embeddings/reindex",
    { project_id: projectId },
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  return response.data;
}

export async function getIndexingStatus(
  accessToken: string,
  projectId: string,
): Promise<EmbeddingQueueStatus> {
  const response = await apiClient.get<EmbeddingQueueStatus>("/embeddings/status", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}

export async function getEmbeddingStatistics(
  accessToken: string,
  projectId: string,
): Promise<EmbeddingStatistics> {
  const response = await apiClient.get<EmbeddingStatistics>("/embeddings/statistics", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}
