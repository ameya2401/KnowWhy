import { useEffect, useState, useCallback } from "react";
import {
  Cpu,
  RefreshCw,
  Play,
  Pause,
  Database,
  CheckCircle2,
  Activity,
  Layers,
  AlertCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  startIndexing,
  pauseIndexing,
  resumeIndexing,
  reindexProject,
  getIndexingStatus,
  getEmbeddingStatistics,
} from "@/services/embeddingsApi";
import type { EmbeddingQueueStatus, EmbeddingStatistics } from "@/types/embeddings";

interface EmbeddingControlsProps {
  projectId: string;
  accessToken: string;
  isMaintainer: boolean;
}

export function EmbeddingControls({
  projectId,
  accessToken,
  isMaintainer,
}: EmbeddingControlsProps) {
  const [statusData, setStatusData] = useState<EmbeddingQueueStatus | null>(null);
  const [statsData, setStatsData] = useState<EmbeddingStatistics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchStatusAndStats = useCallback(async () => {
    try {
      const [status, stats] = await Promise.all([
        getIndexingStatus(accessToken, projectId),
        getEmbeddingStatistics(accessToken, projectId),
      ]);
      setStatusData(status);
      setStatsData(stats);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch embedding info", err);
      setError("Failed to fetch current pipeline status and stats.");
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, projectId]);

  // Initial load
  useEffect(() => {
    void fetchStatusAndStats();
  }, [fetchStatusAndStats]);

  // Polling while status is running
  useEffect(() => {
    if (!statusData || statusData.status !== "running") {
      return;
    }

    const interval = setInterval(() => {
      void fetchStatusAndStats();
    }, 2000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusData?.status, fetchStatusAndStats]);

  const handleStart = async () => {
    if (!isMaintainer) return;
    setActionLoading(true);
    setActionMessage(null);
    try {
      const updated = await startIndexing(accessToken, projectId);
      setStatusData(updated);
      setActionMessage("Indexing pipeline started.");
      void fetchStatusAndStats();
    } catch (err) {
      console.error(err);
      setError("Failed to start indexing.");
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    if (!isMaintainer) return;
    setActionLoading(true);
    setActionMessage(null);
    try {
      const updated = await pauseIndexing(accessToken, projectId);
      setStatusData(updated);
      setActionMessage("Indexing pipeline paused.");
      void fetchStatusAndStats();
    } catch (err) {
      console.error(err);
      setError("Failed to pause indexing.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    if (!isMaintainer) return;
    setActionLoading(true);
    setActionMessage(null);
    try {
      const updated = await resumeIndexing(accessToken, projectId);
      setStatusData(updated);
      setActionMessage("Indexing pipeline resumed.");
      void fetchStatusAndStats();
    } catch (err) {
      console.error(err);
      setError("Failed to resume indexing.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReindex = async () => {
    if (!isMaintainer) return;
    if (
      !confirm(
        "Are you sure you want to rebuild the vector index? This will drop all existing chunks/embeddings and recreate them from scratch.",
      )
    ) {
      return;
    }
    setActionLoading(true);
    setActionMessage(null);
    try {
      const updated = await reindexProject(accessToken, projectId);
      setStatusData(updated);
      setActionMessage("Reindex pipeline initialized.");
      void fetchStatusAndStats();
    } catch (err) {
      console.error(err);
      setError("Failed to rebuild vector index.");
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const status = statusData?.status ?? "idle";
  const processed = statusData?.processed_items ?? 0;
  const total = statusData?.total_items ?? 0;
  const failed = statusData?.failed_items ?? 0;
  const progressPercent = total > 0 ? Math.round((processed / total) * 100) : 0;

  const getStatusBadgeColor = (stat: string) => {
    switch (stat) {
      case "running":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 ring-1 ring-blue-700/10";
      case "paused":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300 ring-1 ring-yellow-700/10";
      case "completed":
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300 ring-1 ring-emerald-700/10";
      case "failed":
        return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 ring-1 ring-red-700/10";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 ring-1 ring-gray-700/10";
    }
  };

  return (
    <div className="grid gap-6 md:grid-cols-3">
      <div className="space-y-6 md:col-span-2">
        {/* Main Status & Controls Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="size-5 text-primary animate-pulse" />
              Pipeline Control Room
            </CardTitle>
            <CardDescription>
              Monitor the status and control the flow of the background vectorization pipeline.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {error && (
              <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-4 text-sm text-destructive border border-destructive/20">
                <AlertCircle className="size-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {actionMessage && (
              <div className="flex items-center gap-2 rounded-md bg-emerald-50 dark:bg-emerald-950/20 p-4 text-sm text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
                <CheckCircle2 className="size-4 shrink-0" />
                <span>{actionMessage}</span>
              </div>
            )}

            {/* Current Pipeline Status */}
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <span className="text-sm font-medium text-muted-foreground block">
                  Current Pipeline Status
                </span>
                <span className="text-lg font-bold capitalize mt-1 inline-flex items-center">
                  {status}
                </span>
              </div>
              <span
                className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase ${getStatusBadgeColor(
                  status,
                )}`}
              >
                {status === "running" && <Activity className="mr-1.5 size-3 animate-pulse" />}
                {status}
              </span>
            </div>

            {/* Progress indicators when running or paused */}
            {(status === "running" || status === "paused" || status === "completed") && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-muted-foreground">Indexing Progress</span>
                  <span className="font-bold">
                    {processed} / {total} documents ({progressPercent}%)
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-500 ease-out"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
                {statusData?.error_message && (
                  <div className="mt-2 text-xs text-red-500 italic">
                    Last failure reason: {statusData.error_message}
                  </div>
                )}
              </div>
            )}

            {/* Actions Panel */}
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Indexing Actions
              </h4>
              <div className="flex flex-wrap gap-3">
                {status !== "running" && (
                  <Button
                    onClick={status === "paused" ? handleResume : handleStart}
                    disabled={actionLoading || !isMaintainer}
                    className="gap-2"
                  >
                    <Play className="size-4" />
                    {status === "paused" ? "Resume Indexing" : "Start Indexing"}
                  </Button>
                )}

                {status === "running" && (
                  <Button
                    variant="outline"
                    onClick={handlePause}
                    disabled={actionLoading || !isMaintainer}
                    className="gap-2"
                  >
                    <Pause className="size-4" />
                    Pause Indexing
                  </Button>
                )}

                <Button
                  variant="destructive"
                  onClick={handleReindex}
                  disabled={actionLoading || !isMaintainer}
                  className="gap-2 ml-auto"
                >
                  <RefreshCw className={`size-4 ${actionLoading ? "animate-spin" : ""}`} />
                  Rebuild Vector Index
                </Button>
              </div>

              {!isMaintainer && (
                <p className="text-xs text-yellow-600 dark:text-yellow-500 bg-yellow-50 dark:bg-yellow-950/20 p-2.5 rounded border border-yellow-500/20 mt-2">
                  Only project maintainers and owners can execute indexing controls.
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Configuration Parameters Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers className="size-5 text-muted-foreground" />
              Pipeline Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2 text-sm">
            <div className="rounded-lg border p-3.5 bg-muted/20">
              <span className="text-xs font-medium text-muted-foreground block">
                Intelligent Chunking Size
              </span>
              <span className="text-base font-semibold text-foreground mt-1 block">
                1000 Characters
              </span>
              <span className="text-xs text-muted-foreground mt-0.5 block">
                Approx. 250 tokens per block.
              </span>
            </div>

            <div className="rounded-lg border p-3.5 bg-muted/20">
              <span className="text-xs font-medium text-muted-foreground block">Chunk Overlap</span>
              <span className="text-base font-semibold text-foreground mt-1 block">
                200 Characters
              </span>
              <span className="text-xs text-muted-foreground mt-0.5 block">
                Ensures semantic continuity.
              </span>
            </div>

            <div className="rounded-lg border p-3.5 bg-muted/20">
              <span className="text-xs font-medium text-muted-foreground block">
                Embedding Provider
              </span>
              <span className="text-base font-semibold text-foreground mt-1 block">OpenAI API</span>
              <span className="text-xs text-muted-foreground mt-0.5 block">
                Normalized embeddings.
              </span>
            </div>

            <div className="rounded-lg border p-3.5 bg-muted/20">
              <span className="text-xs font-medium text-muted-foreground block">
                Vector Model Architecture
              </span>
              <span className="text-base font-semibold text-foreground mt-1 block">
                text-embedding-3-small
              </span>
              <span className="text-xs text-muted-foreground mt-0.5 block">
                1536 Dimensions (L2 Normalized).
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Database Statistics Card */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="size-5 text-primary" />
              Vector Index Statistics
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-lg border p-4 bg-primary/5">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block">
                Total Vector Embeddings
              </span>
              <span className="text-3xl font-extrabold text-foreground mt-1 block">
                {statsData?.total_vectors ?? 0}
              </span>
              <span className="text-xs text-muted-foreground mt-1 block">
                Chunks generated & indexed.
              </span>
            </div>

            <div className="rounded-lg border p-4 bg-muted/30">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block">
                Unique Indexed Entities
              </span>
              <span className="text-2xl font-bold text-foreground mt-1 block">
                {statsData?.indexed_documents ?? 0}
              </span>
              <span className="text-xs text-muted-foreground mt-1 block">
                Connected source documents.
              </span>
            </div>

            <div className="rounded-lg border p-4 bg-muted/30">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block">
                Queue Diagnostics
              </span>
              <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                <div>
                  <span className="text-xs text-muted-foreground block">Pending Jobs</span>
                  <span className="text-lg font-bold text-foreground mt-0.5 block">
                    {statsData?.queue_size ?? 0}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground block">Failed Jobs</span>
                  <span
                    className={`text-lg font-bold mt-0.5 block ${
                      failed > 0 ? "text-destructive" : "text-foreground"
                    }`}
                  >
                    {statsData?.failed_jobs ?? 0}
                  </span>
                </div>
              </div>
            </div>

            {statusData?.last_index_time && (
              <p className="text-[10px] text-muted-foreground italic text-center pt-2">
                Last indexing sync: {new Date(statusData.last_index_time).toLocaleString()}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
