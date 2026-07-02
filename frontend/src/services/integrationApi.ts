import { apiClient } from "@/services/apiClient";

export interface GitHubRepo {
  id: string;
  github_repo_id: string;
  name: string;
  owner: string;
  default_branch: string;
  visibility: string;
  clone_url: string;
  last_sync: string | null;
}

export interface GitHubIntegration {
  id: string;
  status: "connected" | "disconnected" | "syncing" | "error";
  last_sync: string | null;
  last_error: string | null;
  connected_at: string;
}

export interface GetIntegrationResponse {
  connected: boolean;
  integration: GitHubIntegration | null;
  repositories: GitHubRepo[];
}

export interface ListGitHubReposResponse {
  repositories: {
    github_repo_id: string;
    name: string;
    owner: string;
    default_branch: string;
    visibility: string;
    clone_url: string;
  }[];
}

export async function getGitHubIntegration(
  accessToken: string,
  projectId: string,
): Promise<GetIntegrationResponse> {
  const response = await apiClient.get<GetIntegrationResponse>("/integrations/github", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}

export async function connectGitHub(
  accessToken: string,
  payload: { code: string; project_id: string },
): Promise<{ status: string; integration_id: string }> {
  const response = await apiClient.post<{ status: string; integration_id: string }>(
    "/integrations/github/connect",
    payload,
    {
      headers: { Authorization: `Bearer ${accessToken}` },
    },
  );
  return response.data;
}

export async function listGitHubRepositories(
  accessToken: string,
  projectId: string,
): Promise<ListGitHubReposResponse> {
  const response = await apiClient.get<ListGitHubReposResponse>(
    "/integrations/github/repositories",
    {
      headers: { Authorization: `Bearer ${accessToken}` },
      params: { project_id: projectId },
    },
  );
  return response.data;
}

export async function connectGitHubRepository(
  accessToken: string,
  githubRepoId: string,
  payload: {
    project_id: string;
    github_repo_id: string;
    name: string;
    owner: string;
    default_branch: string;
    visibility: string;
    clone_url: string;
  },
): Promise<{ status: string; repository_id: string }> {
  const response = await apiClient.post<{ status: string; repository_id: string }>(
    `/integrations/github/repositories/${githubRepoId}/connect`,
    payload,
    {
      headers: { Authorization: `Bearer ${accessToken}` },
    },
  );
  return response.data;
}

export async function syncGitHubIntegration(
  accessToken: string,
  projectId: string,
): Promise<{ status: string }> {
  const response = await apiClient.post<{ status: string }>(
    "/integrations/github/sync",
    { project_id: projectId },
    {
      headers: { Authorization: `Bearer ${accessToken}` },
    },
  );
  return response.data;
}

export async function disconnectGitHub(
  accessToken: string,
  projectId: string,
): Promise<{ status: string }> {
  const response = await apiClient.delete<{ status: string }>("/integrations/github/disconnect", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}

export interface GitHubDashboardResponse {
  connected: boolean;
  integration: GitHubIntegration | null;
  repositories: GitHubRepo[];
  stats: {
    total_commits: number;
    pull_requests: number;
    open_issues: number;
    contributors: number;
  };
  activity: {
    id: string;
    type: "commit" | "pull_request" | "issue" | "repo_update";
    title: string;
    author: string;
    timestamp: string;
    repository: string;
  }[];
}

export async function getGitHubDashboard(
  accessToken: string,
  projectId: string,
): Promise<GitHubDashboardResponse> {
  const response = await apiClient.get<GitHubDashboardResponse>("/integrations/github/dashboard", {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { project_id: projectId },
  });
  return response.data;
}
