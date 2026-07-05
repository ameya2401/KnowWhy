import { apiClient } from "@/services/apiClient";
import type { EngineeringInsight, EngineeringInsightStatistics } from "@/types/insight";

export async function analyzeProjectInsights(
  accessToken: string,
  projectId: string,
): Promise<EngineeringInsight[]> {
  const response = await apiClient.post<EngineeringInsight[]>(
    "/intelligence/analyze",
    { project_id: projectId },
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  return response.data;
}

export async function listInsights(
  accessToken: string,
  projectId: string,
  params: {
    status?: string;
    severity?: string;
    insight_type?: string;
  } = {},
): Promise<EngineeringInsight[]> {
  const response = await apiClient.get<EngineeringInsight[]>("/intelligence/insights", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId, ...params },
  });
  return response.data;
}

export async function getInsight(
  accessToken: string,
  projectId: string,
  insightId: string,
): Promise<EngineeringInsight> {
  const response = await apiClient.get<EngineeringInsight>(`/intelligence/insights/${insightId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}

export async function getInsightStatistics(
  accessToken: string,
  projectId: string,
): Promise<EngineeringInsightStatistics> {
  const response = await apiClient.get<EngineeringInsightStatistics>("/intelligence/statistics", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}
