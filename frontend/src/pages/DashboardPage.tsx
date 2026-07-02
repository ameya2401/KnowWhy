import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Github,
  AlertCircle,
  RefreshCw,
  Plus,
  ArrowRight,
  GitCommit,
  GitPullRequest,
  AlertOctagon,
  Users,
  Settings,
  HelpCircle,
  ExternalLink,
  Layers,
} from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { useProjects } from "@/projects/ProjectContext";
import {
  getGitHubDashboard,
  syncGitHubIntegration,
  type GitHubDashboardResponse,
} from "@/services/integrationApi";

export function DashboardPage() {
  const { accessToken } = useAuth();
  const { activeProject, projects, isLoading: projectsLoading } = useProjects();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<GitHubDashboardResponse | null>(null);

  const fetchDashboardData = useCallback(async () => {
    if (!accessToken || !activeProject) {
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await getGitHubDashboard(accessToken, activeProject.id);
      setData(res);
    } catch (err: unknown) {
      console.error(err);
      setError("Failed to load dashboard data. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeProject]);

  useEffect(() => {
    void fetchDashboardData();
  }, [fetchDashboardData]);

  const handleSync = async () => {
    if (!accessToken || !activeProject) return;
    setSyncing(true);
    setError(null);
    try {
      await syncGitHubIntegration(accessToken, activeProject.id);
      await fetchDashboardData();
    } catch (err: unknown) {
      console.error(err);
      setError("Sync failed. Check your repository settings or authentication.");
    } finally {
      setSyncing(false);
    }
  };

  const getRelativeTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays === 1) return "Yesterday";
      return `${diffDays} days ago`;
    } catch {
      return dateString;
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "connected":
        return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
      case "syncing":
        return "bg-amber-500/10 text-amber-500 border-amber-500/20 animate-pulse";
      case "error":
        return "bg-rose-500/10 text-rose-500 border-rose-500/20";
      default:
        return "bg-muted text-muted-foreground border-border";
    }
  };

  // Rendering Loading state
  if (projectsLoading) {
    return (
      <DashboardLayout>
        <div className="flex h-[60vh] items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="size-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground font-medium">
              Loading workspace dashboard...
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // Empty state: No projects in organization
  if (projects.length === 0) {
    return (
      <DashboardLayout>
        <div className="flex h-[70vh] items-center justify-center">
          <Card className="max-w-md w-full border border-border shadow-lg">
            <CardHeader className="text-center">
              <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
                <Layers className="size-6" />
              </div>
              <CardTitle className="font-display text-xl font-bold">Create a Project</CardTitle>
              <CardDescription className="text-sm mt-2">
                KnowWhy aggregates intelligence from repositories, tasks, and documentation. Build a
                project to get started.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center pb-6">
              <Button onClick={() => navigate("/projects/new")} className="gap-2">
                <Plus className="size-4" /> Add Project
              </Button>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Top Banner and Summary */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
            {activeProject?.name || "Workspace Dashboard"}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {activeProject?.description ||
              "Sync developer history, commits, and issues for organizational intelligence."}
          </p>
        </div>

        {data?.connected && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSync}
              disabled={syncing || loading}
              className="gap-2 text-xs font-semibold"
            >
              <RefreshCw className={`size-3.5 ${syncing ? "animate-spin" : ""}`} />
              {syncing ? "Syncing..." : "Sync Repository"}
            </Button>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-500">
          <AlertCircle className="size-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Dashboard Grid */}
      {!data?.connected ? (
        // Project connected but no GitHub integrated
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="md:col-span-2 border-border shadow-sm flex flex-col justify-between p-6">
            <div>
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
                <Github className="size-6" />
              </div>
              <h2 className="font-display text-xl font-bold text-foreground">
                Connect Git Repository
              </h2>
              <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                Connect your GitHub repository to KnowWhy to analyze code contributions, track issue
                statuses, link pull requests, and start extracting semantic intelligence.
              </p>
              <div className="grid grid-cols-2 gap-4 mt-6">
                <div className="border rounded-md p-3">
                  <p className="text-xs font-semibold uppercase text-muted-foreground/80 tracking-wider">
                    Automated Ingestion
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Sync commits and metadata in real-time.
                  </p>
                </div>
                <div className="border rounded-md p-3">
                  <p className="text-xs font-semibold uppercase text-muted-foreground/80 tracking-wider">
                    Semantic Reasoner
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Extract technical decisions and codebase structure.
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-8 flex gap-3">
              <Button
                onClick={() => navigate(`/projects/${activeProject?.id}?tab=integrations`)}
                className="gap-2"
              >
                Configure GitHub <ArrowRight className="size-4" />
              </Button>
            </div>
          </Card>

          {/* Quick Actions and Integrations list sidebar for empty state */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <Card className="border-border shadow-sm">
              <CardHeader>
                <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted-foreground/70">
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5">
                <Button
                  variant="outline"
                  className="w-full justify-start text-xs font-medium gap-2"
                  onClick={() => navigate("/projects/new")}
                >
                  <Plus className="size-3.5 text-primary" /> Create New Project
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start text-xs font-medium gap-2"
                  onClick={() => navigate(`/projects/${activeProject?.id}/settings`)}
                >
                  <Settings className="size-3.5 text-muted-foreground" /> Project Settings
                </Button>
              </CardContent>
            </Card>

            {/* Other integrations list */}
            <Card className="border-border shadow-sm">
              <CardHeader>
                <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted-foreground/70 font-display">
                  Integrations
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between p-2 rounded-md border bg-muted/20">
                  <div className="flex items-center gap-2">
                    <Github className="size-4 text-muted-foreground" />
                    <span className="text-xs font-medium">GitHub</span>
                  </div>
                  <span className="text-[10px] border px-2 py-0.5 rounded font-medium bg-red-500/10 text-red-500 border-red-500/15">
                    Not Connected
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-md border border-dashed text-muted-foreground/50 bg-muted/5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium">Notion</span>
                  </div>
                  <span className="text-[9px] border px-1.5 rounded font-mono uppercase tracking-wider">
                    Soon
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-md border border-dashed text-muted-foreground/50 bg-muted/5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium">Google Drive</span>
                  </div>
                  <span className="text-[9px] border px-1.5 rounded font-mono uppercase tracking-wider">
                    Soon
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      ) : (
        // Connected Dashboard layout
        <div className="space-y-6">
          {/* Dashboard Aggregates Stats Row */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-border shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80">
                  Total Commits
                </CardTitle>
                <GitCommit className="size-4 text-primary" />
              </CardHeader>
              <CardContent>
                <p className="font-display text-3xl font-bold tracking-tight">
                  {data.stats.total_commits}
                </p>
                <p className="text-[10px] text-muted-foreground mt-1">
                  Imported from connected repository
                </p>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80">
                  Pull Requests
                </CardTitle>
                <GitPullRequest className="size-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <p className="font-display text-3xl font-bold tracking-tight">
                  {data.stats.pull_requests}
                </p>
                <p className="text-[10px] text-muted-foreground mt-1">Merged, open & closed PRs</p>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80">
                  Open Issues
                </CardTitle>
                <AlertOctagon className="size-4 text-red-500" />
              </CardHeader>
              <CardContent>
                <p className="font-display text-3xl font-bold tracking-tight">
                  {data.stats.open_issues}
                </p>
                <p className="text-[10px] text-muted-foreground mt-1">
                  Outstanding tasks on GitHub
                </p>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80">
                  Contributors
                </CardTitle>
                <Users className="size-4 text-emerald-500" />
              </CardHeader>
              <CardContent>
                <p className="font-display text-3xl font-bold tracking-tight">
                  {data.stats.contributors}
                </p>
                <p className="text-[10px] text-muted-foreground mt-1">
                  Active engineers in history
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Primary Layout columns */}
          <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            {/* Left: Recent Activity timeline feed */}
            <Card className="border-border shadow-sm">
              <CardHeader className="border-b border-border pb-4 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="font-display text-lg font-bold">Recent Activity</CardTitle>
                  <CardDescription className="text-xs">
                    Chronological timeline of commits, PRs, and issues
                  </CardDescription>
                </div>
                <div className="text-[10px] text-muted-foreground font-mono bg-secondary/40 px-2 py-0.5 rounded border border-border">
                  Live Sync Active
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                {data.activity.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <HelpCircle className="size-10 text-muted-foreground/40 mb-3" />
                    <p className="text-sm font-semibold text-foreground">No recent activity</p>
                    <p className="text-xs text-muted-foreground mt-1 max-w-[280px]">
                      The repository is connected, but sync hasn't retrieved any activity. Try
                      triggering a sync.
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleSync}
                      disabled={syncing}
                      className="mt-4 gap-2"
                    >
                      <RefreshCw className={`size-3 ${syncing ? "animate-spin" : ""}`} /> Sync Now
                    </Button>
                  </div>
                ) : (
                  <div className="relative border-l border-border pl-6 space-y-6">
                    {data.activity.map((item, idx) => (
                      <div key={item.id + idx} className="relative">
                        {/* Timeline Bullet Node Icon */}
                        <div className="absolute -left-[31px] top-1.5 flex size-5 items-center justify-center rounded-full bg-background border border-border">
                          {item.type === "commit" && <GitCommit className="size-3 text-primary" />}
                          {item.type === "pull_request" && (
                            <GitPullRequest className="size-3 text-blue-500" />
                          )}
                          {item.type === "issue" && <AlertCircle className="size-3 text-red-500" />}
                        </div>

                        {/* Node Content */}
                        <div>
                          <div className="flex items-center justify-between gap-4">
                            <span className="text-xs font-semibold text-foreground break-all">
                              {item.title}
                            </span>
                            <span className="text-[10px] text-muted-foreground shrink-0 font-mono">
                              {getRelativeTime(item.timestamp)}
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5 mt-1 text-[11px] text-muted-foreground">
                            <span>
                              by{" "}
                              <strong className="font-semibold text-foreground/80">
                                {item.author}
                              </strong>
                            </span>
                            <span>•</span>
                            <span className="font-mono bg-muted/40 px-1 py-0.5 rounded border border-border/40 text-[10px]">
                              {item.repository}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Right: Connected integrations status, repository summary, and Quick Actions */}
            <div className="space-y-6">
              {/* Connected Repositories Summary Card */}
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="font-display text-sm font-bold uppercase tracking-wider text-muted-foreground/85">
                    Connected Repositories
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {data.repositories.map((repo) => (
                    <div
                      key={repo.id}
                      className="border rounded-md p-3 bg-secondary/15 flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-foreground truncate max-w-[150px]">
                            {repo.owner}/{repo.name}
                          </p>
                          <span className="text-[10px] uppercase font-mono tracking-wider font-semibold border px-1.5 rounded bg-muted">
                            {repo.visibility}
                          </span>
                        </div>
                        <p className="text-[10px] text-muted-foreground mt-1">
                          Default Branch: <span className="font-mono">{repo.default_branch}</span>
                        </p>
                      </div>
                      <div className="flex items-center justify-between border-t border-border mt-3 pt-2 text-[10px] text-muted-foreground">
                        <span>
                          Synced {repo.last_sync ? getRelativeTime(repo.last_sync) : "never"}
                        </span>
                        <a
                          href={repo.clone_url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 text-primary hover:underline font-semibold"
                        >
                          Open Repo <ExternalLink className="size-2.5" />
                        </a>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Connected Integrations list */}
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="font-display text-sm font-bold uppercase tracking-wider text-muted-foreground/85">
                    Integrations
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between p-2 rounded-md border bg-card/45">
                    <div className="flex items-center gap-2">
                      <Github className="size-4 text-foreground" />
                      <span className="text-xs font-medium">GitHub</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`text-[10px] border px-2 py-0.5 rounded font-semibold capitalize ${getStatusBadgeClass(data.integration?.status || "connected")}`}
                      >
                        {data.integration?.status || "connected"}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-md border border-dashed text-muted-foreground/50 bg-muted/5">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium">Notion</span>
                    </div>
                    <span className="text-[9px] border px-1.5 rounded font-mono uppercase tracking-wider">
                      Soon
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-md border border-dashed text-muted-foreground/50 bg-muted/5">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium">Google Drive</span>
                    </div>
                    <span className="text-[9px] border px-1.5 rounded font-mono uppercase tracking-wider">
                      Soon
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Actions Panel */}
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="font-display text-sm font-bold uppercase tracking-wider text-muted-foreground/85">
                    Quick Actions
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  <Button
                    variant="outline"
                    className="w-full justify-start text-xs font-medium gap-2"
                    onClick={() => navigate(`/projects/${activeProject?.id}?tab=integrations`)}
                  >
                    <Github className="size-3.5 text-foreground" /> Manage Repositories
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full justify-start text-xs font-medium gap-2"
                    onClick={() => navigate("/projects/new")}
                  >
                    <Plus className="size-3.5 text-primary" /> Create New Project
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full justify-start text-xs font-medium gap-2"
                    onClick={handleSync}
                    disabled={syncing}
                  >
                    <RefreshCw
                      className={`size-3.5 text-muted-foreground ${syncing ? "animate-spin" : ""}`}
                    />
                    Sync Data
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
