import { apiClient } from "@/services/apiClient";
import type {
  KnowledgeItem,
  KnowledgeItemListResponse,
  KnowledgeRelationship,
  KnowledgeSyncLog,
} from "@/types/knowledge";

export async function listKnowledgeItems(
  accessToken: string,
  projectId: string,
  params: {
    source?: string;
    entity_type?: string;
    status?: string;
    search?: string;
    limit?: number;
    offset?: number;
  } = {},
): Promise<KnowledgeItemListResponse> {
  const response = await apiClient.get<KnowledgeItemListResponse>("/knowledge", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId, ...params },
  });
  return response.data;
}

export async function getKnowledgeItem(
  accessToken: string,
  projectId: string,
  itemId: string,
): Promise<KnowledgeItem> {
  const response = await apiClient.get<KnowledgeItem>(`/knowledge/${itemId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}

export async function getKnowledgeItemRelationships(
  accessToken: string,
  projectId: string,
  itemId: string,
): Promise<KnowledgeRelationship[]> {
  const response = await apiClient.get<KnowledgeRelationship[]>(
    `/knowledge/relationships/${itemId}`,
    {
      headers: { Authorization: `Bearer ${accessToken}` },
      params: { project_id: projectId },
    },
  );
  return response.data;
}

export async function getKnowledgeTimeline(
  accessToken: string,
  projectId: string,
  limit = 50,
  offset = 0,
): Promise<KnowledgeItem[]> {
  const response = await apiClient.get<KnowledgeItem[]>("/knowledge/timeline", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId, limit, offset },
  });
  return response.data;
}

export async function syncKnowledge(
  accessToken: string,
  projectId: string,
): Promise<KnowledgeSyncLog> {
  const response = await apiClient.post<KnowledgeSyncLog>(
    "/knowledge/sync",
    { project_id: projectId },
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  return response.data;
}
