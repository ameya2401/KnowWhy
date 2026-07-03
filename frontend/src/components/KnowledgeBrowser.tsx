import { useEffect, useState, useCallback } from "react";
import {
  Search,
  RefreshCw,
  GitCommit,
  GitPullRequest,
  HelpCircle,
  FileText,
  Folder,
  Calendar,
  User,
  ArrowRight,
  Database,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Tag,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Link2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  listKnowledgeItems,
  getKnowledgeItem,
  getKnowledgeItemRelationships,
  getKnowledgeTimeline,
  syncKnowledge,
} from "@/services/knowledgeApi";
import type { KnowledgeItem, KnowledgeRelationship, KnowledgeSyncLog } from "@/types/knowledge";

interface KnowledgeBrowserProps {
  projectId: string;
  accessToken: string;
}

export function KnowledgeBrowser({ projectId, accessToken }: KnowledgeBrowserProps) {
  const [viewMode, setViewMode] = useState<"list" | "timeline">("list");

  // List Filters & Pagination
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [totalItems, setTotalItems] = useState(0);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [entityType, setEntityType] = useState("");
  const [status, setStatus] = useState("");
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);
  const [isItemsLoading, setIsItemsLoading] = useState(false);
  const [itemsError, setItemsError] = useState<string | null>(null);

  // Timeline State
  const [timelineItems, setTimelineItems] = useState<KnowledgeItem[]>([]);
  const [isTimelineLoading, setIsTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);

  // Detail Drawer State
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<KnowledgeItem | null>(null);
  const [relationships, setRelationships] = useState<KnowledgeRelationship[]>([]);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  // Sync State
  const [syncStatus, setSyncStatus] = useState<"idle" | "syncing" | "success" | "error">("idle");
  const [syncLog, setSyncLog] = useState<KnowledgeSyncLog | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  // Load list items
  const loadItems = useCallback(async () => {
    setIsItemsLoading(true);
    setItemsError(null);
    try {
      const res = await listKnowledgeItems(accessToken, projectId, {
        search: search || undefined,
        source: source || undefined,
        entity_type: entityType || undefined,
        status: status || undefined,
        limit,
        offset,
      });
      setItems(res.items);
      setTotalItems(res.total);
    } catch (err: unknown) {
      console.error(err);
      setItemsError("Failed to fetch knowledge items.");
    } finally {
      setIsItemsLoading(false);
    }
  }, [accessToken, projectId, search, source, entityType, status, limit, offset]);

  // Load timeline items
  const loadTimeline = useCallback(async () => {
    setIsTimelineLoading(true);
    setTimelineError(null);
    try {
      const res = await getKnowledgeTimeline(accessToken, projectId, 50, 0);
      setTimelineItems(res);
    } catch (err: unknown) {
      console.error(err);
      setTimelineError("Failed to fetch knowledge timeline.");
    } finally {
      setIsTimelineLoading(false);
    }
  }, [accessToken, projectId]);

  // Handle pagination
  const handlePrevPage = () => {
    if (offset > 0) {
      setOffset(Math.max(0, offset - limit));
    }
  };

  const handleNextPage = () => {
    if (offset + limit < totalItems) {
      setOffset(offset + limit);
    }
  };

  // Trigger sync
  const handleSync = async () => {
    setSyncStatus("syncing");
    setSyncError(null);
    try {
      const log = await syncKnowledge(accessToken, projectId);
      setSyncLog(log);
      if (log.status === "completed") {
        setSyncStatus("success");
        void loadItems();
        if (viewMode === "timeline") {
          void loadTimeline();
        }
      } else if (log.status === "failed") {
        setSyncStatus("error");
        setSyncError(log.error_message || "Sync failed on server.");
      } else {
        // Log is running, start polling
        let attempts = 0;
        const interval = setInterval(async () => {
          attempts++;
          try {
            // Note: Since we don't have a direct get_latest_sync_log endpoint,
            // calling sync again on same project will just trigger normal engine run
            // but we can poll by calling listKnowledgeItems to see if items list updates,
            // or simply wait a moment. For robust UI, we poll the list items after 3 seconds.
            if (attempts > 5) {
              clearInterval(interval);
              setSyncStatus("success");
              void loadItems();
            }
          } catch {
            clearInterval(interval);
          }
        }, 2000);
      }
    } catch (err: unknown) {
      console.error(err);
      setSyncStatus("error");
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setSyncError(axiosError.response?.data?.detail || "Failed to trigger synchronization.");
    }
  };

  // Load detailed item
  useEffect(() => {
    async function loadDetail() {
      if (!selectedItemId) {
        setSelectedItem(null);
        setRelationships([]);
        return;
      }
      setIsDetailLoading(true);
      setDetailError(null);
      try {
        const [itemData, relData] = await Promise.all([
          getKnowledgeItem(accessToken, projectId, selectedItemId),
          getKnowledgeItemRelationships(accessToken, projectId, selectedItemId),
        ]);
        setSelectedItem(itemData);
        setRelationships(relData);
      } catch (err: unknown) {
        console.error(err);
        setDetailError("Failed to load details.");
      } finally {
        setIsDetailLoading(false);
      }
    }
    void loadDetail();
  }, [selectedItemId, accessToken, projectId]);

  // Load initial view
  useEffect(() => {
    if (viewMode === "list") {
      void loadItems();
    } else {
      void loadTimeline();
    }
  }, [viewMode, loadItems, loadTimeline]);

  // Helper: Get source icon
  const getSourceIcon = (src: string, type: string) => {
    switch (src) {
      case "github":
        if (type === "commit") return <GitCommit className="size-4 text-blue-500" />;
        if (type === "pull_request") return <GitPullRequest className="size-4 text-green-500" />;
        return <AlertCircle className="size-4 text-orange-500" />;
      case "notion":
        return <FileText className="size-4 text-purple-500" />;
      case "google_drive":
        if (type === "folder") return <Folder className="size-4 text-yellow-500" />;
        return <FileText className="size-4 text-blue-600" />;
      default:
        return <HelpCircle className="size-4 text-muted-foreground" />;
    }
  };

  const getSourceBadgeColor = (src: string) => {
    switch (src) {
      case "github":
        return "bg-blue-50 text-blue-700 ring-blue-700/10";
      case "notion":
        return "bg-purple-50 text-purple-700 ring-purple-700/10";
      case "google_drive":
        return "bg-yellow-50 text-yellow-800 ring-yellow-700/10";
      default:
        return "bg-gray-50 text-gray-600 ring-gray-600/10";
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
      <div className="space-y-6">
        {/* Top Control Bar */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex rounded-md bg-secondary p-1">
            <button
              onClick={() => setViewMode("list")}
              className={`rounded-sm px-3 py-1.5 text-sm font-medium transition-all ${
                viewMode === "list"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Knowledge List
            </button>
            <button
              onClick={() => setViewMode("timeline")}
              className={`rounded-sm px-3 py-1.5 text-sm font-medium transition-all ${
                viewMode === "timeline"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Timeline View
            </button>
          </div>

          <div className="flex items-center gap-3">
            {syncStatus === "syncing" && (
              <span className="text-xs text-muted-foreground flex items-center gap-1.5">
                <RefreshCw className="size-3 animate-spin" /> Normalizing data...
              </span>
            )}
            {syncStatus === "success" && syncLog && (
              <span className="text-xs text-green-600 flex items-center gap-1.5">
                <CheckCircle className="size-3" /> Normalized {syncLog.items_synced} items,{" "}
                {syncLog.relationships_created} relationships
              </span>
            )}
            {syncStatus === "error" && (
              <span className="text-xs text-red-600 flex items-center gap-1.5">
                <XCircle className="size-3" /> Sync Error: {syncError}
              </span>
            )}
            <Button onClick={handleSync} disabled={syncStatus === "syncing"} className="gap-2">
              <RefreshCw className={`size-4 ${syncStatus === "syncing" ? "animate-spin" : ""}`} />
              Sync Knowledge
            </Button>
          </div>
        </div>

        {viewMode === "list" ? (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Knowledge Store</CardTitle>
              <CardDescription>
                Search and explore aggregated knowledge items normalized from connected
                integrations.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Filter Panel */}
              <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
                <div className="relative">
                  <Search className="absolute left-3 top-3 size-4 text-muted-foreground" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value);
                      setOffset(0);
                    }}
                    placeholder="Search items..."
                    className="h-10 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>

                <select
                  value={source}
                  onChange={(e) => {
                    setSource(e.target.value);
                    setOffset(0);
                  }}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">All Sources</option>
                  <option value="github">GitHub</option>
                  <option value="notion">Notion</option>
                  <option value="google_drive">Google Drive</option>
                </select>

                <select
                  value={entityType}
                  onChange={(e) => {
                    setEntityType(e.target.value);
                    setOffset(0);
                  }}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">All Types</option>
                  <option value="commit">Commit</option>
                  <option value="pull_request">Pull Request</option>
                  <option value="issue">Issue</option>
                  <option value="notion_page">Notion Page</option>
                  <option value="document">Document</option>
                  <option value="folder">Folder</option>
                </select>

                <select
                  value={status}
                  onChange={(e) => {
                    setStatus(e.target.value);
                    setOffset(0);
                  }}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">All Statuses</option>
                  <option value="active">Active</option>
                  <option value="archived">Archived</option>
                </select>
              </div>

              {/* Items List */}
              {isItemsLoading ? (
                <div className="flex h-48 items-center justify-center">
                  <RefreshCw className="size-6 animate-spin text-muted-foreground" />
                </div>
              ) : itemsError ? (
                <div className="rounded-md bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-700/10">
                  {itemsError}
                </div>
              ) : items.length === 0 ? (
                <div className="flex h-48 flex-col items-center justify-center gap-2 border border-dashed rounded-md">
                  <Database className="size-8 text-muted-foreground" />
                  <p className="text-sm font-medium text-muted-foreground">
                    No knowledge items found.
                  </p>
                  <p className="text-xs text-muted-foreground">Try triggering a sync above.</p>
                </div>
              ) : (
                <div className="divide-y divide-border border rounded-md">
                  {items.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => setSelectedItemId(item.id)}
                      className={`flex flex-col gap-2 p-4 transition-colors hover:bg-muted/50 cursor-pointer ${
                        selectedItemId === item.id ? "bg-muted" : ""
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-center gap-2">
                          {getSourceIcon(item.source, item.entity_type)}
                          <h4 className="font-semibold text-foreground leading-tight hover:underline">
                            {item.title}
                          </h4>
                        </div>
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getSourceBadgeColor(
                            item.source,
                          )}`}
                        >
                          {item.source}
                        </span>
                      </div>

                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {item.description || "No description provided."}
                      </p>

                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                        {item.author && (
                          <span className="flex items-center gap-1">
                            <User className="size-3" /> {item.author}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Calendar className="size-3" />{" "}
                          {new Date(item.updated_time).toLocaleDateString()}
                        </span>
                        {item.tags && item.tags.length > 0 && (
                          <div className="flex gap-1.5">
                            {item.tags.slice(0, 3).map((t) => (
                              <span
                                key={t}
                                className="inline-flex items-center gap-0.5 rounded bg-secondary px-1 py-0.5 text-[10px] text-secondary-foreground font-medium"
                              >
                                <Tag className="size-2" /> {t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Pagination */}
              {totalItems > limit && (
                <div className="flex items-center justify-between pt-2">
                  <p className="text-xs text-muted-foreground">
                    Showing {offset + 1} to {Math.min(offset + limit, totalItems)} of {totalItems}{" "}
                    items
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handlePrevPage}
                      disabled={offset === 0}
                    >
                      <ChevronLeft className="size-4 mr-1" /> Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleNextPage}
                      disabled={offset + limit >= totalItems}
                    >
                      Next <ChevronRight className="size-4 ml-1" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Knowledge Timeline</CardTitle>
              <CardDescription>
                A chronological activity feed of changes across all integrations.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isTimelineLoading ? (
                <div className="flex h-48 items-center justify-center">
                  <RefreshCw className="size-6 animate-spin text-muted-foreground" />
                </div>
              ) : timelineError ? (
                <div className="rounded-md bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-700/10">
                  {timelineError}
                </div>
              ) : timelineItems.length === 0 ? (
                <div className="flex h-48 flex-col items-center justify-center gap-2 border border-dashed rounded-md">
                  <Clock className="size-8 text-muted-foreground" />
                  <p className="text-sm font-medium text-muted-foreground">
                    No chronological events found.
                  </p>
                </div>
              ) : (
                <div className="relative border-l border-border pl-6 ml-3 space-y-6">
                  {timelineItems.map((item) => (
                    <div
                      key={item.id}
                      className="relative group cursor-pointer"
                      onClick={() => setSelectedItemId(item.id)}
                    >
                      {/* Timeline marker */}
                      <span className="absolute -left-9 top-1.5 flex size-6 items-center justify-center rounded-full bg-background border border-border ring-4 ring-background">
                        {getSourceIcon(item.source, item.entity_type)}
                      </span>

                      <div>
                        <span className="text-xs text-muted-foreground flex items-center gap-1 mb-1">
                          <Calendar className="size-3" />{" "}
                          {new Date(item.updated_time).toLocaleString()}
                        </span>
                        <h4 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                          {item.title}
                        </h4>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          {item.description || "No description provided."}
                        </p>
                        <div className="flex gap-2 items-center mt-2 text-xs">
                          <span
                            className={`rounded-full px-1.5 py-0.5 font-medium ${getSourceBadgeColor(item.source)}`}
                          >
                            {item.source}
                          </span>
                          <span className="text-muted-foreground">•</span>
                          <span className="text-muted-foreground capitalize">
                            {item.entity_type}
                          </span>
                          {item.author && (
                            <>
                              <span className="text-muted-foreground">•</span>
                              <span className="text-muted-foreground">{item.author}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Detail Panel */}
      <div className="space-y-6">
        <Card className="h-[calc(100vh-220px)] overflow-y-auto sticky top-6">
          <CardHeader>
            <CardTitle className="text-lg">Entity Details</CardTitle>
            <CardDescription>
              Select an item to view its properties and relationship graph connections.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {!selectedItemId ? (
              <div className="flex h-64 flex-col items-center justify-center gap-2 text-center text-muted-foreground">
                <Database className="size-8" />
                <p className="text-sm font-medium">No entity selected.</p>
                <p className="text-xs">
                  Click on any item in the list or timeline to view details.
                </p>
              </div>
            ) : isDetailLoading ? (
              <div className="flex h-64 items-center justify-center">
                <RefreshCw className="size-6 animate-spin text-muted-foreground" />
              </div>
            ) : detailError || !selectedItem ? (
              <div className="rounded-md bg-red-50 p-4 text-xs text-red-700 ring-1 ring-red-700/10">
                {detailError || "Failed to load entity detail."}
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${getSourceBadgeColor(selectedItem.source)}`}
                    >
                      {selectedItem.source}
                    </span>
                    <span className="inline-flex items-center rounded-full bg-gray-100 text-gray-800 text-[10px] font-medium px-2 py-0.5 capitalize">
                      {selectedItem.entity_type}
                    </span>
                  </div>
                  <h3 className="font-semibold text-foreground text-base leading-snug">
                    {selectedItem.title}
                  </h3>
                  {selectedItem.url && (
                    <a
                      href={selectedItem.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-flex items-center text-xs text-primary hover:underline gap-1 font-medium"
                    >
                      Open Original Document <ExternalLink className="size-3" />
                    </a>
                  )}
                </div>

                <div className="space-y-3 pt-4 border-t border-border">
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Properties
                  </h4>
                  <div className="space-y-2 text-xs">
                    {selectedItem.author && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Author:</span>
                        <span className="font-medium text-foreground">{selectedItem.author}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Created:</span>
                      <span className="font-medium text-foreground">
                        {new Date(selectedItem.created_time).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Modified:</span>
                      <span className="font-medium text-foreground">
                        {new Date(selectedItem.updated_time).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Status:</span>
                      <span className="font-medium text-foreground capitalize">
                        {selectedItem.status}
                      </span>
                    </div>
                  </div>
                </div>

                {selectedItem.description && (
                  <div className="space-y-2 pt-4 border-t border-border">
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Description
                    </h4>
                    <p className="text-xs text-foreground bg-muted p-2 rounded leading-relaxed whitespace-pre-wrap">
                      {selectedItem.description}
                    </p>
                  </div>
                )}

                {selectedItem.content && (
                  <div className="space-y-2 pt-4 border-t border-border">
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Content
                    </h4>
                    <div className="max-h-48 overflow-y-auto text-xs text-foreground bg-muted p-2.5 rounded font-mono leading-relaxed whitespace-pre-wrap">
                      {selectedItem.content}
                    </div>
                  </div>
                )}

                {/* Relationships section */}
                <div className="space-y-3 pt-4 border-t border-border">
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
                    <Link2 className="size-3" /> Graph Relationships ({relationships.length})
                  </h4>
                  {relationships.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic">
                      No relationships mapped for this item.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {relationships.map((rel) => {
                        const isSource = rel.source_item_id === selectedItem.id;
                        const related = isSource ? rel.target_item : rel.source_item;
                        if (!related) return null;

                        return (
                          <div
                            key={rel.id}
                            onClick={() => setSelectedItemId(related.id)}
                            className="flex items-center justify-between gap-2 rounded border border-border bg-card p-2 text-xs transition-colors hover:bg-muted cursor-pointer"
                          >
                            <div className="flex flex-col gap-0.5">
                              <span className="font-medium text-foreground line-clamp-1 hover:underline">
                                {related.title}
                              </span>
                              <span className="text-[10px] text-muted-foreground flex items-center gap-1.5">
                                {isSource ? (
                                  <>
                                    <span>outward</span>
                                    <ArrowRight className="size-2.5" />
                                    <span className="rounded-full bg-primary/10 text-primary px-1 py-0.5 text-[9px] font-bold uppercase">
                                      {rel.relationship_type}
                                    </span>
                                  </>
                                ) : (
                                  <>
                                    <span>inward</span>
                                    <ArrowRight className="size-2.5 rotate-180" />
                                    <span className="rounded-full bg-secondary text-secondary-foreground px-1 py-0.5 text-[9px] font-bold uppercase">
                                      {rel.relationship_type}
                                    </span>
                                  </>
                                )}
                              </span>
                            </div>
                            <span className="text-[10px] font-semibold text-muted-foreground bg-secondary px-1 py-0.5 rounded">
                              {Math.round(rel.confidence * 100)}%
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {selectedItem.metadata_json &&
                  Object.keys(selectedItem.metadata_json).length > 0 && (
                    <div className="space-y-2 pt-4 border-t border-border">
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Raw Metadata
                      </h4>
                      <pre className="max-h-40 overflow-auto text-[10px] text-muted-foreground bg-muted p-2 rounded leading-tight">
                        {JSON.stringify(selectedItem.metadata_json, null, 2)}
                      </pre>
                    </div>
                  )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
