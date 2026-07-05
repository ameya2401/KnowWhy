import { apiClient } from "./apiClient";
import { GraphResponse, EntityDetailResponse, TimelineResponse } from "../types/graph";
import { KnowledgeRelationship } from "../types/knowledge";

export const graphApi = {
  getGraph: async (
    projectId: string,
    limit = 500,
    offset = 0,
    entityTypes?: string[],
  ): Promise<GraphResponse> => {
    const params = new URLSearchParams({
      project_id: projectId,
      limit: String(limit),
      offset: String(offset),
    });
    if (entityTypes && entityTypes.length > 0) {
      entityTypes.forEach((t) => params.append("entity_type", t));
    }
    const response = await apiClient.get<GraphResponse>(`/graph?${params.toString()}`);
    return response.data;
  },

  getEntityDetail: async (entityId: string, projectId: string): Promise<EntityDetailResponse> => {
    const response = await apiClient.get<EntityDetailResponse>(
      `/graph/entity/${entityId}?project_id=${projectId}`,
    );
    return response.data;
  },

  getTimeline: async (
    projectId: string,
    filters?: {
      entityType?: string;
      source?: string;
      author?: string;
      startDate?: string;
      endDate?: string;
      limit?: number;
      offset?: number;
    },
  ): Promise<TimelineResponse> => {
    const params = new URLSearchParams({
      project_id: projectId,
      ...(filters?.limit !== undefined && { limit: String(filters.limit) }),
      ...(filters?.offset !== undefined && { offset: String(filters.offset) }),
      ...(filters?.entityType && { entity_type: filters.entityType }),
      ...(filters?.source && { source: filters.source }),
      ...(filters?.author && { author: filters.author }),
      ...(filters?.startDate && { start_date: filters.startDate }),
      ...(filters?.endDate && { end_date: filters.endDate }),
    });
    const response = await apiClient.get<TimelineResponse>(`/timeline?${params.toString()}`);
    return response.data;
  },

  getProjectTimeline: async (
    projectId: string,
    filters?: {
      entityType?: string;
      source?: string;
      author?: string;
      startDate?: string;
      endDate?: string;
      limit?: number;
      offset?: number;
    },
  ): Promise<TimelineResponse> => {
    const params = new URLSearchParams({
      ...(filters?.limit !== undefined && { limit: String(filters.limit) }),
      ...(filters?.offset !== undefined && { offset: String(filters.offset) }),
      ...(filters?.entityType && { entity_type: filters.entityType }),
      ...(filters?.source && { source: filters.source }),
      ...(filters?.author && { author: filters.author }),
      ...(filters?.startDate && { start_date: filters.startDate }),
      ...(filters?.endDate && { end_date: filters.endDate }),
    });
    const response = await apiClient.get<TimelineResponse>(
      `/timeline/project/${projectId}?${params.toString()}`,
    );
    return response.data;
  },

  getNodeRelationships: async (
    nodeId: string,
    projectId: string,
  ): Promise<KnowledgeRelationship[]> => {
    const response = await apiClient.get<KnowledgeRelationship[]>(
      `/relationships/${nodeId}?project_id=${projectId}`,
    );
    return response.data;
  },
};
