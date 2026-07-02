import { useEffect, useState, useCallback, useMemo } from "react";
import {
  RefreshCw,
  GitCommit,
  GitPullRequest,
  AlertCircle,
  HelpCircle,
  Clock,
  Filter,
} from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { useProjects } from "@/projects/ProjectContext";
import { getGitHubDashboard, type GitHubDashboardResponse } from "@/services/integrationApi";

export function ActivityPage() {
  const { accessToken } = useAuth();
  const { activeProject } = useProjects();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<GitHubDashboardResponse | null>(null);
  const [filterType, setFilterType] = useState<"all" | "commit" | "pull_request" | "issue">("all");

  const fetchActivity = useCallback(async () => {
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
      setError("Failed to fetch activity log.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeProject]);

  useEffect(() => {
    void fetchActivity();
  }, [fetchActivity]);

  const filteredActivity = useMemo(() => {
    if (!data?.activity) return [];
    if (filterType === "all") return data.activity;
    return data.activity.filter((item) => item.type === filterType);
  }, [data, filterType]);

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

  return (
    <DashboardLayout>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
            Activity Log
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Browse through commits, pull requests, and issues synchronized from your workspace
            repositories.
          </p>
        </div>

        {activeProject && (
          <Button
            variant="outline"
            size="sm"
            onClick={fetchActivity}
            disabled={loading}
            className="gap-2 text-xs font-semibold self-start sm:self-auto"
          >
            <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Log
          </Button>
        )}
      </div>

      {!activeProject ? (
        <Card className="border-border shadow-sm p-6 text-center">
          <HelpCircle className="size-10 text-muted-foreground/45 mx-auto mb-3" />
          <p className="text-sm font-semibold text-foreground">No active project selected</p>
          <p className="text-xs text-muted-foreground mt-1">
            Please select or create a project to view the activity log.
          </p>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-1">
            <Filter className="size-3.5 text-muted-foreground shrink-0" />
            <button
              onClick={() => setFilterType("all")}
              className={`px-3 py-1 text-xs font-semibold rounded-full border transition-all ${
                filterType === "all"
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-background text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              All Activity
            </button>
            <button
              onClick={() => setFilterType("commit")}
              className={`px-3 py-1 text-xs font-semibold rounded-full border transition-all ${
                filterType === "commit"
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-background text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Commits
            </button>
            <button
              onClick={() => setFilterType("pull_request")}
              className={`px-3 py-1 text-xs font-semibold rounded-full border transition-all ${
                filterType === "pull_request"
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-background text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Pull Requests
            </button>
            <button
              onClick={() => setFilterType("issue")}
              className={`px-3 py-1 text-xs font-semibold rounded-full border transition-all ${
                filterType === "issue"
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-background text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Issues
            </button>
          </div>

          {/* Activity Timeline List */}
          <Card className="border border-border shadow-sm">
            <CardContent className="pt-6">
              {loading && !data ? (
                <div className="flex justify-center py-12">
                  <RefreshCw className="size-6 animate-spin text-primary" />
                </div>
              ) : error ? (
                <p className="text-sm text-red-500 text-center py-6">{error}</p>
              ) : filteredActivity.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Clock className="size-8 mx-auto text-muted-foreground/30 mb-2" />
                  <p className="text-sm font-semibold">No activities found</p>
                  <p className="text-xs mt-1">
                    There are no records matching your selected filter type.
                  </p>
                </div>
              ) : (
                <div className="relative border-l border-border pl-6 space-y-6">
                  {filteredActivity.map((item, idx) => (
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
                          <span className="text-sm font-semibold text-foreground">
                            {item.title}
                          </span>
                          <span className="text-xs text-muted-foreground shrink-0 font-mono">
                            {getRelativeTime(item.timestamp)}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground">
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
        </div>
      )}
    </DashboardLayout>
  );
}
