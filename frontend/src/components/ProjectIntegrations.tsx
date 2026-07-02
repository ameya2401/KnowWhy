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
  const [data, setData] = useState<GetIntegrationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Repository selection state
  const [availableRepos, setAvailableRepos] = useState<AvailableRepo[]>([]);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [repoSearch, setRepoSearch] = useState("");
  const [selectedRepoIds, setSelectedRepoIds] = useState<string[]>([]);
  const [showManageRepos, setShowManageRepos] = useState(false);

  // Syncing state
  const [isSyncingLocal, setIsSyncingLocal] = useState(false);

  // Mock code input for easier manual testing
  const [mockCode, setMockCode] = useState("");
  const [showMockForm, setShowMockForm] = useState(false);

  const fetchIntegrationStatus = useCallback(async () => {
    try {
      const res = await getGitHubIntegration(accessToken, projectId);
      setData(res);
      if (res.integration?.status === "syncing") {
        setIsSyncingLocal(true);
      } else {
        setIsSyncingLocal(false);
      }
    } catch (err) {
      console.error("Failed to load integrations", err);
      setError("Failed to load integrations status.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, projectId]);

  useEffect(() => {
    void fetchIntegrationStatus();
  }, [fetchIntegrationStatus]);

  // Polling during sync
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;
    if (isSyncingLocal) {
      intervalId = setInterval(() => {
        void fetchIntegrationStatus();
      }, 4000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isSyncingLocal, fetchIntegrationStatus]);

  const handleConnectRedirect = () => {
    const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID || "";
    if (!clientId) {
      setError("GitHub Client ID is not configured in the environment.");
      setShowMockForm(true);
      return;
    }
    const redirectUri = `${window.location.origin}/integrations/github/callback`;
    const scope = "repo,user";
    const state = projectId;
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(
      redirectUri,
    )}&scope=${scope}&state=${state}`;
  };

  const handleMockConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mockCode.trim()) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await connectGitHub(accessToken, { code: mockCode.trim(), project_id: projectId });
      setSuccess("Successfully connected GitHub integration (mock token).");
      setMockCode("");
      setShowMockForm(false);
      await fetchIntegrationStatus();
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.response?.data?.detail ?? "Failed to connect using mock token.");
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (
      !confirm(
        "Are you sure you want to disconnect GitHub? All repository connections will be lost.",
      )
    ) {
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await disconnectGitHub(accessToken, projectId);
      setSuccess("GitHub integration disconnected successfully.");
      await fetchIntegrationStatus();
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.response?.data?.detail ?? "Failed to disconnect integration.");
    } finally {
      setLoading(false);
    }
  };

  const handleLoadAvailableRepos = async () => {
    setLoadingRepos(true);
    setError(null);
    try {
      const res = await listGitHubRepositories(accessToken, projectId);
      setAvailableRepos(res.repositories);
      setSelectedRepoIds([]);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.response?.data?.detail ?? "Failed to load GitHub repositories.");
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
    setLoading(true);
    setError(null);
    setSuccess(null);
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
      setSuccess(`Successfully connected ${selectedRepoIds.length} repositories.`);
      setShowManageRepos(false);
      await fetchIntegrationStatus();
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.response?.data?.detail ?? "Failed to connect repositories.");
    } finally {
      setLoading(false);
    }
  };

  const handleSyncNow = async () => {
    setIsSyncingLocal(true);
    setError(null);
    setSuccess(null);
    try {
      await syncGitHubIntegration(accessToken, projectId);
      setSuccess("Sync request triggered. Syncing database records in background...");
      await fetchIntegrationStatus();
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.response?.data?.detail ?? "Failed to sync metadata.");
      setIsSyncingLocal(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <RefreshCw className="size-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Loading integrations...</span>
      </div>
    );
  }

  const isConnected = data?.connected ?? false;
  const integration = data?.integration;
  const linkedRepos = data?.repositories ?? [];

  const filteredAvailableRepos = availableRepos.filter(
    (repo) =>
      repo.name.toLowerCase().includes(repoSearch.toLowerCase()) ||
      repo.owner.toLowerCase().includes(repoSearch.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      {error && (
        <div className="flex items-start gap-3 rounded-md bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-700/10">
          <AlertCircle className="size-5 shrink-0 text-red-600" />
          <div>{error}</div>
        </div>
      )}

      {success && (
        <div className="flex items-start gap-3 rounded-md bg-emerald-50 p-4 text-sm text-emerald-700 ring-1 ring-emerald-700/10">
          <CheckCircle2 className="size-5 shrink-0 text-emerald-600" />
          <div>{success}</div>
        </div>
      )}

      {!isConnected ? (
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
                <Button onClick={handleConnectRedirect}>
                  <Github className="mr-2 size-5" /> Connect GitHub OAuth
                </Button>

                <button
                  type="button"
                  onClick={() => setShowMockForm(!showMockForm)}
                  className="text-xs text-muted-foreground hover:text-foreground underline"
                >
                  Local testing or manual token configuration?
                </button>

                {showMockForm && (
                  <form
                    onSubmit={handleMockConnect}
                    className="w-full max-w-sm mt-4 p-4 border rounded-md bg-muted/40 space-y-3"
                  >
                    <p className="text-xs text-muted-foreground">
                      Paste a GitHub Personal Access Token or OAuth code to connect:
                    </p>
                    <input
                      type="password"
                      className="h-9 w-full rounded-md border bg-background px-3 text-xs outline-none focus:ring-1 focus:ring-ring"
                      placeholder="ghp_..."
                      value={mockCode}
                      onChange={(e) => setMockCode(e.target.value)}
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
                    {integration?.connected_at
                      ? new Date(integration.connected_at).toLocaleString()
                      : ""}
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  {isMaintainer && (
                    <Button variant="outline" size="sm" onClick={handleDisconnect}>
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
                      {integration?.status === "syncing" && (
                        <RefreshCw className="size-3.5 animate-spin text-blue-500" />
                      )}
                      {integration?.status === "connected" && (
                        <span className="size-2 rounded-full bg-emerald-500" />
                      )}
                      {integration?.status === "error" && (
                        <span className="size-2 rounded-full bg-red-500" />
                      )}
                      {integration?.status}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-xs">Last Synced</span>
                    <span className="font-semibold mt-0.5 block">
                      {integration?.last_sync
                        ? new Date(integration.last_sync).toLocaleString()
                        : "Never"}
                    </span>
                  </div>
                </div>
                {integration?.last_error && (
                  <div className="rounded-md bg-red-50 p-3 text-xs text-red-800 border border-red-200">
                    <span className="font-semibold">Last error:</span> {integration.last_error}
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
                  <span>Linked Repositories: {linkedRepos.length}</span>
                </div>
                <Button
                  className="w-full"
                  disabled={isSyncingLocal || linkedRepos.length === 0}
                  onClick={handleSyncNow}
                >
                  <RefreshCw className={`mr-2 size-4 ${isSyncingLocal ? "animate-spin" : ""}`} />
                  {isSyncingLocal ? "Syncing..." : "Sync Now"}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Linked Repositories */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <div>
                <CardTitle>Linked Repositories</CardTitle>
                <CardDescription>GitHub repositories currently syncing metadata.</CardDescription>
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
              {linkedRepos.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  No repositories linked. Click "Link Repository" to get started.
                </div>
              ) : (
                <div className="divide-y border rounded-md">
                  {linkedRepos.map((repo) => (
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
                            {repo.last_sync ? new Date(repo.last_sync).toLocaleString() : "Never"}
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
                  ) : filteredAvailableRepos.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground text-sm">
                      No repositories found.
                    </div>
                  ) : (
                    <div className="border rounded-md divide-y max-h-[40vh] overflow-y-auto bg-background">
                      {filteredAvailableRepos.map((repo) => {
                        const isAlreadyLinked = linkedRepos.some(
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
                    disabled={selectedRepoIds.length === 0 || loading}
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
  );
}
