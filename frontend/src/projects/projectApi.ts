import { apiClient } from "@/services/apiClient";
import type {
  Project,
  ProjectCreatePayload,
  ProjectMember,
  ProjectMemberInvitePayload,
  ProjectRole,
} from "@/projects/types";

export async function listProjects(accessToken: string): Promise<Project[]> {
  const response = await apiClient.get<Project[]>("/projects", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}

export async function createProject(
  accessToken: string,
  payload: ProjectCreatePayload,
): Promise<Project> {
  const response = await apiClient.post<Project>("/projects", payload, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}

export async function getProject(accessToken: string, projectId: string): Promise<Project> {
  const response = await apiClient.get<Project>(`/projects/${projectId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}

export async function updateProject(
  accessToken: string,
  projectId: string,
  payload: Partial<ProjectCreatePayload>,
): Promise<Project> {
  const response = await apiClient.put<Project>(`/projects/${projectId}`, payload, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}

export async function deleteProject(accessToken: string, projectId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export async function archiveProject(accessToken: string, projectId: string): Promise<Project> {
  const response = await apiClient.post<Project>(
    `/projects/${projectId}/archive`,
    {},
    {
      headers: { Authorization: `Bearer ${accessToken}` },
    },
  );
  return response.data;
}

export async function listProjectMembers(
  accessToken: string,
  projectId: string,
): Promise<ProjectMember[]> {
  const response = await apiClient.get<ProjectMember[]>(`/projects/${projectId}/members`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}

export async function inviteProjectMember(
  accessToken: string,
  projectId: string,
  payload: ProjectMemberInvitePayload,
): Promise<ProjectMember> {
  const response = await apiClient.post<ProjectMember>(`/projects/${projectId}/members`, payload, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}

export async function updateProjectMemberRole(
  accessToken: string,
  projectId: string,
  membershipId: string,
  role: ProjectRole,
): Promise<ProjectMember> {
  const response = await apiClient.put<ProjectMember>(
    `/projects/${projectId}/members/${membershipId}`,
    { role },
    {
      headers: { Authorization: `Bearer ${accessToken}` },
    },
  );
  return response.data;
}

export async function removeProjectMember(
  accessToken: string,
  projectId: string,
  membershipId: string,
): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/members/${membershipId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}
