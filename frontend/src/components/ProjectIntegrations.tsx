import { useEffect, useState, useCallback } from "react";
import {
  Github,
  AlertCircle,
  RefreshCw,
  Link2,
  Search,
  CheckCircle2,
  AlertTriangle,
  Database,
  FileText,
  ExternalLink,
  Layers,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getGitHubIntegration,
  disconnectGitHub,
  listGitHubRepositories,
  connectGitHubRepository,
  syncGitHubIntegration,
  connectGitHub,
  type GetIntegrationResponse,
  getNotionIntegration,
  connectNotion,
  syncNotionIntegration,
  disconnectNotion,
  type NotionDashboardResponse,
} from "@/services/integrationApi";

interface ProjectIntegrationsProps {
  projectId: string;
  accessToken: string;
  isMaintainer: boolean;
}

interface AvailableRepo {
  github_repo_id: string;
  name: string;
  owner: string;
  default_branch: string;
  visibility: string;
  clone_url: string;
}

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
}

export function ProjectIntegrations({
  projectId,
  accessToken,
  isMaintainer,
}: ProjectIntegrationsProps) {
  const [activeTab, setActiveTab] = useState<"github" | "notion">("github");

  // GitHub States
  const [githubData, setGithubData] = useState<GetIntegrationResponse | null>(null);
  const [githubLoading, setGithubLoading] = useState(true);
  const [githubError, setGithubError] = useState<string | null>(null);
  const [githubSuccess, setGithubSuccess] = useState<string | null>(null);
  const [isGithubSyncing, setIsGithubSyncing] = useState(false);
  const [availableRepos, setAvailableRepos] = useState<AvailableRepo[]>([]);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [repoSearch, setRepoSearch] = useState("");
  const [selectedRepoIds, setSelectedRepoIds] = useState<string[]>([]);
  const [showManageRepos, setShowManageRepos] = useState(false);
  const [showGithubMockForm, setShowGithubMockForm] = useState(false);
  const [githubMockCode, setGithubMockCode] = useState("");

  // Notion States
  const [notionData, setNotionData] = useState<NotionDashboardResponse | null>(null);
  const [notionLoading, setNotionLoading] = useState(true);
  const [notionError, setNotionError] = useState<string | null>(null);
  const [notionSuccess, setNotionSuccess] = useState<string | null>(null);
  const [isNotionSyncing, setIsNotionSyncing] = useState(false);
  const [showNotionMockForm, setShowNotionMockForm] = useState(false);
  const [notionMockCode, setNotionMockCode] = useState("");

  // Fetch GitHub Status
  const fetchGithubStatus = useCallback(async () => {
    try {
      const res = await getGitHubIntegration(accessToken, projectId);
      setGithubData(res);
      if (res.integration?.status === "syncing") {
        setIsGithubSyncing(true);
      } else {
        setIsGithubSyncing(false);
      }
    } catch (err) {
      console.error("Failed to load GitHub integration", err);
      setGithubError("Failed to load GitHub integration status.");
    } finally {
      setGithubLoading(false);
    }
  }, [accessToken, projectId]);

  // Fetch Notion Status
  const fetchNotionStatus = useCallback(async () => {
    try {
      const res = await getNotionIntegration(accessToken, projectId);
      setNotionData(res);
      if (res.integration?.status === "syncing") {
        setIsNotionSyncing(true);
      } else {
        setIsNotionSyncing(false);
      }
    } catch (err) {
      console.error("Failed to load Notion integration", err);
      setNotionError("Failed to load Notion integration status.");
    } finally {
      setNotionLoading(false);
    }
  }, [accessToken, projectId]);

  useEffect(() => {
    void fetchGithubStatus();
    void fetchNotionStatus();
  }, [fetchGithubStatus, fetchNotionStatus]);

  // Polling during GitHub sync
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;
    if (isGithubSyncing) {
      intervalId = setInterval(() => {
        void fetchGithubStatus();
      }, 4000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isGithubSyncing, fetchGithubStatus]);

  // Polling during Notion sync
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;
    if (isNotionSyncing) {
      intervalId = setInterval(() => {
        void fetchNotionStatus();
      }, 4000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isNotionSyncing, fetchNotionStatus]);

  // GitHub Actions
  const handleGithubRedirect = () => {
    const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID || "";
    if (!clientId) {
      setGithubError("GitHub Client ID is not configured in the environment.");
      setShowGithubMockForm(true);
      return;
    }
    const redirectUri = `${window.location.origin}/integrations/github/callback`;
    const scope = "repo,user";
    const state = projectId;
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(
      redirectUri,
    )}&scope=${scope}&state=${state}`;
  };

  const handleGithubMockConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubMockCode.trim()) return;
    setGithubLoading(true);
    setGithubError(null);
    setGithubSuccess(null);
    try {
      await connectGitHub(accessToken, { code: githubMockCode.trim(), project_id: projectId });
      setGithubSuccess("Successfully connected GitHub integration (mock token).");
      setGithubMockCode("");
      setShowGithubMockForm(false);
      await fetchGithubStatus();
    } catch (err) {
      const apiErr = err as ApiError;
      setGithubError(apiErr.response?.data?.detail ?? "Failed to connect using mock token.");
    } finally {
      setGithubLoading(false);
    }
  };

  const handleGithubDisconnect = async () => {
    if (
      !confirm(
        "Are you sure you want to disconnect GitHub? All repository connections will be lost.",
      )
    ) {
      return;
    }
    setGithubLoading(true);
    setGithubError(null);
    setGithubSuccess(null);
    try {
      await disconnectGitHub(accessToken, projectId);
      setGithubSuccess("GitHub integration disconnected successfully.");
      await fetchGithubStatus();
    } catch (err) {
      const apiErr = err as ApiError;
      setGithubError(apiErr.response?.data?.detail ?? "Failed to disconnect integration.");
    } finally {
      setGithubLoading(false);
    }
  };

  const handleLoadAvailableRepos = async () => {
    setLoadingRepos(true);
    setGithubError(null);
    try {
      const res = await listGitHubRepositories(accessToken, projectId);
      setAvailableRepos(res.repositories);
      setSelectedRepoIds([]);
    } catch (err) {
      const apiErr = err as ApiError;
      setGithubError(apiErr.response?.data?.detail ?? "Failed to load GitHub repositories.");
    } finally {
      setLoadingRepos(false);
    }
  };

  const handleToggleRepoSelect = (repoId: string) => {
    setSelectedRepoIds((prev) =>
      prev.includes(repoId) ? prev.filter((id) => id !== repoId) : [...prev, repoId],
    );
  };

  const handleLinkRepositories = async () => {
    if (selectedRepoIds.length === 0) return;
    setGithubLoading(true);
    setGithubError(null);
    setGithubSuccess(null);
    try {
      for (const repoId of selectedRepoIds) {
        const repoData = availableRepos.find((r) => r.github_repo_id === repoId);
        if (repoData) {
          await connectGitHubRepository(accessToken, repoId, {
            project_id: projectId,
            github_repo_id: repoId,
            name: repoData.name,
            owner: repoData.owner,
            default_branch: repoData.default_branch,
            visibility: repoData.visibility,
            clone_url: repoData.clone_url,
          });
        }
      }
      setGithubSuccess(`Successfully connected ${selectedRepoIds.length} repositories.`);
      setShowManageRepos(false);
      await fetchGithubStatus();
    } catch (err) {
      const apiErr = err as ApiError;
      setGithubError(apiErr.response?.data?.detail ?? "Failed to connect repositories.");
    } finally {
      setGithubLoading(false);
    }
  };

  const handleGithubSyncNow = async () => {
    setIsGithubSyncing(true);
    setGithubError(null);
    setGithubSuccess(null);
    try {
      await syncGitHubIntegration(accessToken, projectId);
      setGithubSuccess("Sync request triggered. Syncing database records in background...");
      await fetchGithubStatus();
    } catch (err) {
      const apiErr = err as ApiError;
      setGithubError(apiErr.response?.data?.detail ?? "Failed to sync metadata.");
      setIsGithubSyncing(false);
    }
  };

  // Notion Actions
  const handleNotionRedirect = () => {
    const clientId = import.meta.env.VITE_NOTION_CLIENT_ID || "";
    if (!clientId) {
      setNotionError("Notion Client ID is not configured in the environment.");
      setShowNotionMockForm(true);
      return;
    }
    const redirectUri = `${window.location.origin}/integrations/notion/callback`;
    const state = projectId;
    window.location.href = `https://api.notion.com/v1/oauth/authorize?client_id=${clientId}&response_type=code&owner=user&redirect_uri=${encodeURIComponent(
      redirectUri,
    )}&state=${state}`;
  };

  const handleNotionMockConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notionMockCode.trim()) return;
    setNotionLoading(true);
    setNotionError(null);
    setNotionSuccess(null);
    try {
      await connectNotion(accessToken, { code: notionMockCode.trim(), project_id: projectId });
      setNotionSuccess("Successfully connected Notion integration (mock token).");
      setNotionMockCode("");
      setShowNotionMockForm(false);
      await fetchNotionStatus();
    } catch (err) {
      const apiErr = err as ApiError;
      setNotionError(apiErr.response?.data?.detail ?? "Failed to connect using mock token.");
    } finally {
      setNotionLoading(false);
    }
  };

  const handleNotionDisconnect = async () => {
    if (
      !confirm("Are you sure you want to disconnect Notion? All synced Notion pages will be lost.")
    ) {
      return;
    }
    setNotionLoading(true);
    setNotionError(null);
    setNotionSuccess(null);
    try {
      await disconnectNotion(accessToken, projectId);
      setNotionSuccess("Notion integration disconnected successfully.");
      await fetchNotionStatus();
    } catch (err) {
      const apiErr = err as ApiError;
      setNotionError(apiErr.response?.data?.detail ?? "Failed to disconnect integration.");
    } finally {
      setNotionLoading(false);
    }
  };

  const handleNotionSyncNow = async () => {
    setIsNotionSyncing(true);
    setNotionError(null);
    setNotionSuccess(null);
    try {
      await syncNotionIntegration(accessToken, projectId);
      setNotionSuccess("Notion sync request triggered. Syncing pages in background...");
      await fetchNotionStatus();
    } catch (err) {
      const apiErr = err as ApiError;
      setNotionError(apiErr.response?.data?.detail ?? "Failed to sync Notion metadata.");
      setIsNotionSyncing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Tabs Header */}
      <div className="flex border-b border-muted">
        <button
          onClick={() => setActiveTab("github")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-all ${
            activeTab === "github"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Github className="size-4" />
          GitHub
        </button>
        <button
          onClick={() => setActiveTab("notion")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-all ${
            activeTab === "notion"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Layers className="size-4" />
          Notion
        </button>
      </div>

      {activeTab === "github" && (
        <div className="space-y-6">
          {githubError && (
            <div className="flex items-start gap-3 rounded-md bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-700/10">
              <AlertCircle className="size-5 shrink-0 text-red-600" />
              <div>{githubError}</div>
            </div>
          )}

          {githubSuccess && (
            <div className="flex items-start gap-3 rounded-md bg-emerald-50 p-4 text-sm text-emerald-700 ring-1 ring-emerald-700/10">
              <CheckCircle2 className="size-5 shrink-0 text-emerald-600" />
              <div>{githubSuccess}</div>
            </div>
          )}

          {githubLoading && !githubData ? (
            <div className="flex h-48 items-center justify-center">
              <RefreshCw className="size-8 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">
                Loading GitHub integration...
              </span>
            </div>
          ) : !githubData?.connected ? (
            <Card className="border-dashed">
              <CardHeader className="text-center">
                <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-secondary text-foreground">
                  <Github className="size-6" />
                </div>
                <CardTitle className="mt-4">Connect GitHub Integration</CardTitle>
                <CardDescription className="max-w-md mx-auto">
                  Link GitHub repositories to import commits, pull requests, and issues. Connected
                  repositories sync automatically.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col items-center gap-4">
                {isMaintainer ? (
                  <>
                    <Button onClick={handleGithubRedirect}>
                      <Github className="mr-2 size-5" /> Connect GitHub OAuth
                    </Button>

                    <button
                      type="button"
                      onClick={() => setShowGithubMockForm(!showGithubMockForm)}
                      className="text-xs text-muted-foreground hover:text-foreground underline"
                    >
                      Local testing or manual token configuration?
                    </button>

                    {showGithubMockForm && (
                      <form
                        onSubmit={handleGithubMockConnect}
                        className="w-full max-w-sm mt-4 p-4 border rounded-md bg-muted/40 space-y-3"
                      >
                        <p className="text-xs text-muted-foreground">
                          Paste a GitHub Personal Access Token or OAuth code to connect:
                        </p>
                        <input
                          type="password"
                          className="h-9 w-full rounded-md border bg-background px-3 text-xs outline-none focus:ring-1 focus:ring-ring"
                          placeholder="ghp_..."
                          value={githubMockCode}
                          onChange={(e) => setGithubMockCode(e.target.value)}
                          required
                        />
                        <Button type="submit" size="sm" className="w-full">
                          Link Token Directly
                        </Button>
                      </form>
                    )}
                  </>
                ) : (
                  <div className="flex items-center gap-2 rounded-md bg-amber-50 p-3 text-xs text-amber-800 border border-amber-200">
                    <AlertTriangle className="size-4 shrink-0 text-amber-600" />
                    Only project owners or maintainers can configure integrations.
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Integration Header Card */}
              <div className="grid gap-6 md:grid-cols-3">
                <Card className="md:col-span-2">
                  <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Github className="size-5" /> GitHub Connection
                      </CardTitle>
                      <CardDescription>
                        Connected at{" "}
                        {githubData.integration?.connected_at
                          ? new Date(githubData.integration.connected_at).toLocaleString()
                          : ""}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      {isMaintainer && (
                        <Button variant="outline" size="sm" onClick={handleGithubDisconnect}>
                          Disconnect
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 pt-2 border-t text-sm">
                      <div>
                        <span className="text-muted-foreground block text-xs">Status</span>
                        <span className="font-semibold capitalize flex items-center gap-1.5 mt-0.5">
                          {githubData.integration?.status === "syncing" && (
                            <RefreshCw className="size-3.5 animate-spin text-blue-500" />
                          )}
                          {githubData.integration?.status === "connected" && (
                            <span className="size-2 rounded-full bg-emerald-500" />
                          )}
                          {githubData.integration?.status === "error" && (
                            <span className="size-2 rounded-full bg-red-500" />
                          )}
                          {githubData.integration?.status}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block text-xs">Last Synced</span>
                        <span className="font-semibold mt-0.5 block">
                          {githubData.integration?.last_sync
                            ? new Date(githubData.integration.last_sync).toLocaleString()
                            : "Never"}
                        </span>
                      </div>
                    </div>
                    {githubData.integration?.last_error && (
                      <div className="rounded-md bg-red-50 p-3 text-xs text-red-800 border border-red-200">
                        <span className="font-semibold">Last error:</span>{" "}
                        {githubData.integration.last_error}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Sync Controls</CardTitle>
                    <CardDescription>Request immediate synchronization</CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-3">
                    <div className="text-xs text-muted-foreground flex items-center gap-2">
                      <Database className="size-4 shrink-0" />
                      <span>Linked Repositories: {githubData.repositories.length}</span>
                    </div>
                    <Button
                      className="w-full"
                      disabled={isGithubSyncing || githubData.repositories.length === 0}
                      onClick={handleGithubSyncNow}
                    >
                      <RefreshCw
                        className={`mr-2 size-4 ${isGithubSyncing ? "animate-spin" : ""}`}
                      />
                      {isGithubSyncing ? "Syncing..." : "Sync Now"}
                    </Button>
                  </CardContent>
                </Card>
              </div>

              {/* Linked Repositories */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                  <div>
                    <CardTitle>Linked Repositories</CardTitle>
                    <CardDescription>
                      GitHub repositories currently syncing metadata.
                    </CardDescription>
                  </div>
                  {isMaintainer && (
                    <Button
                      size="sm"
                      onClick={() => {
                        setShowManageRepos(true);
                        void handleLoadAvailableRepos();
                      }}
                    >
                      <Link2 className="mr-2 size-4" /> Link Repository
                    </Button>
                  )}
                </CardHeader>
                <CardContent>
                  {githubData.repositories.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground text-sm">
                      No repositories linked. Click "Link Repository" to get started.
                    </div>
                  ) : (
                    <div className="divide-y border rounded-md">
                      {githubData.repositories.map((repo) => (
                        <div
                          key={repo.id}
                          className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 gap-2"
                        >
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm">
                                {repo.owner}/{repo.name}
                              </span>
                              <span className="rounded bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground font-mono">
                                {repo.default_branch}
                              </span>
                              <span className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground capitalize">
                                {repo.visibility}
                              </span>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1 break-all">
                              {repo.clone_url}
                            </p>
                          </div>
                          <div className="flex items-center gap-4 text-xs">
                            <div>
                              <span className="text-muted-foreground">Last sync: </span>
                              <span className="font-medium">
                                {repo.last_sync
                                  ? new Date(repo.last_sync).toLocaleString()
                                  : "Never"}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Manage Repositories Modal Backdrop */}
              {showManageRepos && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
                  <div className="w-full max-w-2xl bg-card border rounded-lg shadow-lg flex flex-col max-h-[85vh]">
                    <div className="p-6 border-b flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold">Link GitHub Repositories</h3>
                        <p className="text-sm text-muted-foreground">
                          Select repositories from your GitHub account to connect to KnowWhy.
                        </p>
                      </div>
                      <button
                        onClick={() => setShowManageRepos(false)}
                        className="text-muted-foreground hover:text-foreground text-xl"
                      >
                        &times;
                      </button>
                    </div>

                    <div className="p-6 flex-1 overflow-y-auto space-y-4">
                      <div className="flex items-center gap-2 border rounded-md px-3 bg-background">
                        <Search className="size-4 text-muted-foreground shrink-0" />
                        <input
                          type="text"
                          className="h-10 w-full bg-transparent text-sm outline-none"
                          placeholder="Search repositories..."
                          value={repoSearch}
                          onChange={(e) => setRepoSearch(e.target.value)}
                        />
                      </div>

                      {loadingRepos ? (
                        <div className="flex h-32 items-center justify-center text-sm text-muted-foreground gap-2">
                          <RefreshCw className="size-5 animate-spin" /> Loading repos...
                        </div>
                      ) : (
                        <div className="border rounded-md divide-y max-h-[40vh] overflow-y-auto bg-background">
                          {availableRepos
                            .filter(
                              (repo) =>
                                repo.name.toLowerCase().includes(repoSearch.toLowerCase()) ||
                                repo.owner.toLowerCase().includes(repoSearch.toLowerCase()),
                            )
                            .map((repo) => {
                              const isAlreadyLinked = githubData.repositories.some(
                                (lr) => lr.github_repo_id === repo.github_repo_id,
                              );
                              return (
                                <div
                                  key={repo.github_repo_id}
                                  className={`flex items-center justify-between p-3 text-sm ${
                                    isAlreadyLinked ? "bg-muted/40" : ""
                                  }`}
                                >
                                  <div className="flex items-center gap-3">
                                    <input
                                      type="checkbox"
                                      className="size-4 rounded border-input"
                                      disabled={isAlreadyLinked}
                                      checked={selectedRepoIds.includes(repo.github_repo_id)}
                                      onChange={() => handleToggleRepoSelect(repo.github_repo_id)}
                                    />
                                    <div>
                                      <span className="font-medium">
                                        {repo.owner}/{repo.name}
                                      </span>
                                      <span className="ml-2 text-xs text-muted-foreground">
                                        ({repo.visibility})
                                      </span>
                                    </div>
                                  </div>
                                  {isAlreadyLinked ? (
                                    <span className="text-xs text-muted-foreground italic mr-2">
                                      Linked
                                    </span>
                                  ) : null}
                                </div>
                              );
                            })}
                        </div>
                      )}
                    </div>

                    <div className="p-6 border-t flex justify-end gap-3 bg-muted/20">
                      <Button variant="outline" onClick={() => setShowManageRepos(false)}>
                        Cancel
                      </Button>
                      <Button
                        onClick={handleLinkRepositories}
                        disabled={selectedRepoIds.length === 0 || githubLoading}
                      >
                        Link {selectedRepoIds.length} selected
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === "notion" && (
        <div className="space-y-6">
          {notionError && (
            <div className="flex items-start gap-3 rounded-md bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-700/10">
              <AlertCircle className="size-5 shrink-0 text-red-600" />
              <div>{notionError}</div>
            </div>
          )}

          {notionSuccess && (
            <div className="flex items-start gap-3 rounded-md bg-emerald-50 p-4 text-sm text-emerald-700 ring-1 ring-emerald-700/10">
              <CheckCircle2 className="size-5 shrink-0 text-emerald-600" />
              <div>{notionSuccess}</div>
            </div>
          )}

          {notionLoading && !notionData ? (
            <div className="flex h-48 items-center justify-center">
              <RefreshCw className="size-8 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">
                Loading Notion integration...
              </span>
            </div>
          ) : !notionData?.connected ? (
            <Card className="border-dashed">
              <CardHeader className="text-center">
                <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-secondary text-foreground">
                  <Layers className="size-6 text-indigo-500" />
                </div>
                <CardTitle className="mt-4">Connect Notion Integration</CardTitle>
                <CardDescription className="max-w-md mx-auto">
                  Authorize access to your Notion workspace to synchronize documentation, notes,
                  databases, and custom knowledge pages directly into KnowWhy.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col items-center gap-4">
                {isMaintainer ? (
                  <>
                    <Button
                      onClick={handleNotionRedirect}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white"
                    >
                      <Layers className="mr-2 size-5" /> Connect Notion Workspace
                    </Button>

                    <button
                      type="button"
                      onClick={() => setShowNotionMockForm(!showNotionMockForm)}
                      className="text-xs text-muted-foreground hover:text-foreground underline"
                    >
                      Local testing or manual token configuration?
                    </button>

                    {showNotionMockForm && (
                      <form
                        onSubmit={handleNotionMockConnect}
                        className="w-full max-w-sm mt-4 p-4 border rounded-md bg-muted/40 space-y-3"
                      >
                        <p className="text-xs text-muted-foreground">
                          Paste a Notion access token or authorization code to connect:
                        </p>
                        <input
                          type="password"
                          className="h-9 w-full rounded-md border bg-background px-3 text-xs outline-none focus:ring-1 focus:ring-ring"
                          placeholder="secret_..."
                          value={notionMockCode}
                          onChange={(e) => setNotionMockCode(e.target.value)}
                          required
                        />
                        <Button
                          type="submit"
                          size="sm"
                          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                        >
                          Link Token Directly
                        </Button>
                      </form>
                    )}
                  </>
                ) : (
                  <div className="flex items-center gap-2 rounded-md bg-amber-50 p-3 text-xs text-amber-800 border border-amber-200">
                    <AlertTriangle className="size-4 shrink-0 text-amber-600" />
                    Only project owners or maintainers can configure integrations.
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Integration Header Card */}
              <div className="grid gap-6 md:grid-cols-3">
                <Card className="md:col-span-2">
                  <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Layers className="size-5 text-indigo-500" /> Notion Workspace Connection
                      </CardTitle>
                      <CardDescription>
                        Connected to{" "}
                        <span className="font-semibold text-foreground">
                          {notionData.integration?.workspace_name || "Notion Workspace"}
                        </span>{" "}
                        at{" "}
                        {notionData.integration?.connected_at
                          ? new Date(notionData.integration.connected_at).toLocaleString()
                          : ""}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      {isMaintainer && (
                        <Button variant="outline" size="sm" onClick={handleNotionDisconnect}>
                          Disconnect
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 pt-2 border-t text-sm">
                      <div>
                        <span className="text-muted-foreground block text-xs">Status</span>
                        <span className="font-semibold capitalize flex items-center gap-1.5 mt-0.5">
                          {notionData.integration?.status === "syncing" && (
                            <RefreshCw className="size-3.5 animate-spin text-indigo-500" />
                          )}
                          {notionData.integration?.status === "connected" && (
                            <span className="size-2 rounded-full bg-emerald-500" />
                          )}
                          {notionData.integration?.status === "error" && (
                            <span className="size-2 rounded-full bg-red-500" />
                          )}
                          {notionData.integration?.status}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block text-xs">Last Synced</span>
                        <span className="font-semibold mt-0.5 block">
                          {notionData.integration?.last_sync
                            ? new Date(notionData.integration.last_sync).toLocaleString()
                            : "Never"}
                        </span>
                      </div>
                    </div>
                    {notionData.integration?.last_error && (
                      <div className="rounded-md bg-red-50 p-3 text-xs text-red-800 border border-red-200">
                        <span className="font-semibold">Last error:</span>{" "}
                        {notionData.integration.last_error}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Sync Controls</CardTitle>
                    <CardDescription>Request immediate page indexing</CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-3">
                    <div className="text-xs text-muted-foreground flex items-center gap-2">
                      <FileText className="size-4 shrink-0 text-indigo-500" />
                      <span>Synced Pages: {notionData.pages.length}</span>
                    </div>
                    <Button
                      className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                      disabled={isNotionSyncing}
                      onClick={handleNotionSyncNow}
                    >
                      <RefreshCw
                        className={`mr-2 size-4 ${isNotionSyncing ? "animate-spin" : ""}`}
                      />
                      {isNotionSyncing ? "Indexing..." : "Sync Pages"}
                    </Button>
                  </CardContent>
                </Card>
              </div>

              {/* Synced Notion Pages */}
              <Card>
                <CardHeader>
                  <CardTitle>Synced Notion Pages</CardTitle>
                  <CardDescription>
                    All document items and subpages fetched from the workspace.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {notionData.pages.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground text-sm">
                      No Notion pages indexed yet. Click "Sync Pages" to crawl the workspace.
                    </div>
                  ) : (
                    <div className="overflow-x-auto border rounded-md">
                      <table className="w-full text-left border-collapse text-sm">
                        <thead>
                          <tr className="bg-muted/40 border-b">
                            <th className="p-3 font-medium text-xs text-muted-foreground">Title</th>
                            <th className="p-3 font-medium text-xs text-muted-foreground">
                              Author
                            </th>
                            <th className="p-3 font-medium text-xs text-muted-foreground">
                              Last Edited
                            </th>
                            <th className="p-3 font-medium text-xs text-muted-foreground text-right">
                              Link
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {notionData.pages.map((page) => (
                            <tr key={page.id} className="hover:bg-muted/20">
                              <td className="p-3">
                                <div className="font-semibold text-foreground flex items-center gap-2">
                                  <FileText className="size-4 text-indigo-500 shrink-0" />
                                  <span>{page.title || "Untitled Document"}</span>
                                  {page.archived && (
                                    <span className="text-[10px] bg-red-100 text-red-800 rounded px-1 py-0.5">
                                      Archived
                                    </span>
                                  )}
                                </div>
                                <div className="text-xs text-muted-foreground font-mono mt-0.5">
                                  ID: {page.notion_page_id}
                                </div>
                              </td>
                              <td className="p-3 text-muted-foreground">
                                {page.author || "Unknown"}
                              </td>
                              <td className="p-3 text-muted-foreground">
                                {new Date(page.last_edited_time).toLocaleString()}
                              </td>
                              <td className="p-3 text-right">
                                <a
                                  href={page.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-900 font-medium"
                                >
                                  Open in Notion
                                  <ExternalLink className="size-3" />
                                </a>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
