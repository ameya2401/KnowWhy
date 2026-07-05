import { useEffect, useState, useCallback, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Search,
  SlidersHorizontal,
  Calendar,
  User,
  Tag,
  ExternalLink,
  ArrowRight,
  Database,
  Link2,
  GitCommit,
  GitPullRequest,
  AlertCircle,
  FileText,
  Folder,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Clock,
  Sparkles,
} from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { useProjects } from "@/projects/ProjectContext";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  searchKnowledge,
  getSearchSuggestions,
  getRecentSearches,
  getAvailableFilters,
  searchHybridKnowledge,
  getSearchStatistics,
  triggerSearchReindex,
} from "@/services/searchApi";
import { getKnowledgeItem, getKnowledgeItemRelationships } from "@/services/knowledgeApi";
import type { KnowledgeItem, KnowledgeRelationship } from "@/types/knowledge";
import type {
  SearchResult,
  HybridSearchResult,
  AvailableFilters,
  SearchStatisticsResponse,
} from "@/types/search";

export function SearchPage() {
  const { accessToken } = useAuth();
  const { activeProject } = useProjects();
  const [searchParams, setSearchParams] = useSearchParams();

  // Search Parameters & Results
  const [q, setQ] = useState(() => searchParams.get("q") || "");
  const [results, setResults] = useState<(SearchResult | HybridSearchResult)[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Hybrid Search Mode State
  const [searchMode, setSearchMode] = useState<"standard" | "hybrid">("hybrid");
  const [similarityThreshold, setSimilarityThreshold] = useState(0.3);
  const [stats, setStats] = useState<SearchStatisticsResponse | null>(null);
  const [isReindexing, setIsReindexing] = useState(false);

  // Filters State
  const [availableFilters, setAvailableFilters] = useState<AvailableFilters>({
    sources: [],
    entity_types: [],
    authors: [],
    tags: [],
  });
  const [source, setSource] = useState("");
  const [entityType, setEntityType] = useState("");
  const [author, setAuthor] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [sortBy, setSortBy] = useState("relevance");

  // Pagination
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);

  // Autocomplete Suggestions & History
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [recentQueries, setRecentQueries] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Detail Drawer State
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<KnowledgeItem | null>(null);
  const [relationships, setRelationships] = useState<KnowledgeRelationship[]>([]);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  // Load search statistics
  const loadStats = useCallback(async () => {
    if (!accessToken || !activeProject) return;
    try {
      const data = await getSearchStatistics(accessToken, activeProject.id);
      setStats(data);
    } catch (err) {
      console.error("Failed to load search statistics", err);
    }
  }, [accessToken, activeProject]);

  // Handle re-indexing trigger
  const handleReindex = async () => {
    if (!accessToken || !activeProject) return;
    setIsReindexing(true);
    try {
      await triggerSearchReindex(accessToken, activeProject.id);
      setTimeout(() => {
        void loadStats();
        setIsReindexing(false);
      }, 1500);
    } catch (err) {
      console.error("Reindexing failed", err);
      setIsReindexing(false);
    }
  };

  // Fetch available filters and recent searches
  const loadFiltersAndHistory = useCallback(async () => {
    if (!accessToken || !activeProject) return;
    try {
      const [filterData, historyData] = await Promise.all([
        getAvailableFilters(accessToken, activeProject.id),
        getRecentSearches(accessToken, activeProject.id),
      ]);
      setAvailableFilters(filterData);
      setRecentQueries(historyData.queries || []);
      void loadStats();
    } catch (err) {
      console.error("Failed to load filters or history", err);
    }
  }, [accessToken, activeProject, loadStats]);

  // Execute Search
  const executeSearch = useCallback(async () => {
    if (!accessToken || !activeProject) return;
    setIsLoading(true);
    setError(null);
    try {
      if (searchMode === "hybrid") {
        const res = await searchHybridKnowledge(accessToken, activeProject.id, {
          q: q || undefined,
          source: source || undefined,
          entity_type: entityType || undefined,
          author: author || undefined,
          tags: selectedTags.length > 0 ? selectedTags.join(",") : undefined,
          date_start: dateStart || undefined,
          date_end: dateEnd || undefined,
          similarity_threshold: similarityThreshold,
          limit,
          offset,
        });
        setResults(res.results);
        setTotal(res.total);
      } else {
        const res = await searchKnowledge(accessToken, activeProject.id, {
          q: q || undefined,
          source: source || undefined,
          entity_type: entityType || undefined,
          author: author || undefined,
          tags: selectedTags.length > 0 ? selectedTags.join(",") : undefined,
          date_start: dateStart || undefined,
          date_end: dateEnd || undefined,
          sort_by: sortBy,
          limit,
          offset,
        });
        setResults(res.results);
        setTotal(res.total);
      }

      // Refresh recent searches to include the new query
      if (q.trim()) {
        const historyData = await getRecentSearches(accessToken, activeProject.id);
        setRecentQueries(historyData.queries || []);
      }
      void loadStats();
    } catch (err) {
      console.error(err);
      setError("Failed to execute search query.");
    } finally {
      setIsLoading(false);
    }
  }, [
    accessToken,
    activeProject,
    q,
    source,
    entityType,
    author,
    selectedTags,
    dateStart,
    dateEnd,
    sortBy,
    limit,
    offset,
    searchMode,
    similarityThreshold,
    loadStats,
  ]);

  // Handle typing & autocomplete suggestions
  const handleInputChange = async (val: string) => {
    setQ(val);
    if (!accessToken || !activeProject || !val.trim()) {
      setSuggestions([]);
      return;
    }
    try {
      const res = await getSearchSuggestions(accessToken, activeProject.id, val, 6);
      setSuggestions(res.suggestions);
    } catch {
      setSuggestions([]);
    }
  };

  // Click suggestion or history item
  const handleSelectQuery = (queryText: string) => {
    setQ(queryText);
    setSearchParams({ q: queryText });
    setShowSuggestions(false);
    setOffset(0);
  };

  // Form Submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchParams({ q });
    setShowSuggestions(false);
    setOffset(0);
  };

  // Clear all filters
  const handleClearFilters = () => {
    setSource("");
    setEntityType("");
    setAuthor("");
    setSelectedTags([]);
    setDateStart("");
    setDateEnd("");
    setSortBy("relevance");
    setOffset(0);
  };

  // Toggle single tag
  const handleToggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
    setOffset(0);
  };

  // Load detailed item details when selectedItemId changes
  useEffect(() => {
    async function loadDetail() {
      if (!selectedItemId || !accessToken || !activeProject) {
        setSelectedItem(null);
        setRelationships([]);
        return;
      }
      setIsDetailLoading(true);
      setDetailError(null);
      try {
        const [itemData, relData] = await Promise.all([
          getKnowledgeItem(accessToken, activeProject.id, selectedItemId),
          getKnowledgeItemRelationships(accessToken, activeProject.id, selectedItemId),
        ]);
        setSelectedItem(itemData);
        setRelationships(relData);
      } catch (err) {
        console.error(err);
        setDetailError("Failed to load entity details.");
      } finally {
        setIsDetailLoading(false);
      }
    }
    void loadDetail();
  }, [selectedItemId, accessToken, activeProject]);

  // Reload when project, search params, offset or sort change
  useEffect(() => {
    const queryParam = searchParams.get("q") || "";
    setQ(queryParam);
    void loadFiltersAndHistory();
    void executeSearch();
  }, [searchParams, activeProject, offset, sortBy, executeSearch, loadFiltersAndHistory]);

  // Helpers for UI
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
        return "bg-blue-50 text-blue-700 ring-blue-700/10 dark:bg-blue-900/30 dark:text-blue-300";
      case "notion":
        return "bg-purple-50 text-purple-700 ring-purple-700/10 dark:bg-purple-900/30 dark:text-purple-300";
      case "google_drive":
        return "bg-yellow-50 text-yellow-800 ring-yellow-700/10 dark:bg-yellow-900/30 dark:text-yellow-300";
      default:
        return "bg-gray-50 text-gray-600 ring-gray-600/10 dark:bg-gray-800 dark:text-gray-300";
    }
  };

  // Text highlighting logic for queries
  const renderHighlightedText = (text: string | null, searchTerms: string) => {
    if (!text) return "No description available.";
    if (!searchTerms.trim()) return text;

    const terms = searchTerms
      .split(/\s+/)
      .filter((t) => t.length > 1)
      .map((t) => t.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&"));

    if (terms.length === 0) return text;

    const regex = new RegExp(`(${terms.join("|")})`, "gi");
    const parts = text.split(regex);

    return (
      <>
        {parts.map((part, i) =>
          regex.test(part) ? (
            <mark
              key={i}
              className="bg-yellow-200 dark:bg-yellow-800 text-foreground font-semibold px-0.5 rounded"
            >
              {part}
            </mark>
          ) : (
            part
          ),
        )}
      </>
    );
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Top Search bar with Autocomplete */}
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="font-display text-3xl font-semibold tracking-tight">Search Engine</h2>
              <p className="text-sm text-muted-foreground">
                Query, filter, and explore all connected knowledge bases in real-time.
              </p>
            </div>

            {/* Search Mode Toggle */}
            <div className="flex items-center bg-muted p-1 rounded-lg border border-border shadow-inner">
              <button
                type="button"
                onClick={() => {
                  setSearchMode("standard");
                  setOffset(0);
                }}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 flex items-center gap-1.5 ${
                  searchMode === "standard"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Search className="size-3.5" />
                Keyword Search
              </button>
              <button
                type="button"
                onClick={() => {
                  setSearchMode("hybrid");
                  setOffset(0);
                }}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 flex items-center gap-1.5 ${
                  searchMode === "hybrid"
                    ? "bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Sparkles className="size-3.5" />
                Hybrid AI Search
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="relative w-full max-w-3xl">
            <div className="relative">
              <Search className="absolute left-3 top-3.5 size-5 text-muted-foreground" />
              <input
                ref={searchInputRef}
                type="text"
                value={q}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                onChange={(e) => handleInputChange(e.target.value)}
                placeholder="Search by keywords, titles, tags, or authors..."
                className="h-12 w-full rounded-lg border border-input bg-card pl-10 pr-24 text-sm outline-none focus:ring-2 focus:ring-primary shadow-sm"
              />
              <div className="absolute right-2 top-2 flex gap-1">
                <Button type="submit" size="sm">
                  Search
                </Button>
              </div>
            </div>

            {/* Suggestions Dropdown */}
            {showSuggestions && (q.trim() || recentQueries.length > 0) && (
              <div className="absolute top-13 left-0 w-full rounded-md border border-border bg-card shadow-lg z-50 p-2 space-y-2 max-h-80 overflow-y-auto">
                {/* Autocomplete Suggestions */}
                {suggestions.length > 0 && (
                  <div>
                    <p className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60">
                      Suggestions
                    </p>
                    {suggestions.map((sug) => (
                      <button
                        key={sug}
                        type="button"
                        onClick={() => handleSelectQuery(sug)}
                        className="w-full text-left px-2 py-1.5 text-xs hover:bg-accent rounded transition-colors flex items-center gap-2"
                      >
                        <Search className="size-3 text-muted-foreground" />
                        <span className="truncate">{sug}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Search History */}
                {recentQueries.length > 0 && (
                  <div>
                    <p className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 flex items-center gap-1">
                      <Clock className="size-3" /> Recent Searches
                    </p>
                    {recentQueries.slice(0, 5).map((query) => (
                      <button
                        key={query}
                        type="button"
                        onClick={() => handleSelectQuery(query)}
                        className="w-full text-left px-2 py-1.5 text-xs hover:bg-accent rounded transition-colors flex items-center gap-2 text-muted-foreground hover:text-foreground"
                      >
                        <Search className="size-3 text-muted-foreground/50" />
                        <span className="truncate">{query}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </form>
        </div>

        {/* Workspace Layout */}
        <div className="grid gap-6 lg:grid-cols-[260px_1fr_360px]">
          {/* Advanced Filters Sidebar */}
          <aside className="space-y-6">
            <Card>
              <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <SlidersHorizontal className="size-4" /> Filters
                </CardTitle>
                <button
                  onClick={handleClearFilters}
                  className="text-xs text-primary hover:underline font-medium"
                >
                  Clear All
                </button>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                {/* Sort By Option or Similarity Threshold */}
                {searchMode === "standard" ? (
                  <div className="space-y-1.5">
                    <label className="font-semibold text-muted-foreground uppercase tracking-wider text-[10px]">
                      Sort By
                    </label>
                    <select
                      value={sortBy}
                      onChange={(e) => {
                        setSortBy(e.target.value);
                        setOffset(0);
                      }}
                      className="h-9 w-full rounded-md border border-input bg-background px-3 text-xs outline-none focus:ring-1 focus:ring-ring"
                    >
                      <option value="relevance">Relevance</option>
                      <option value="newest">Newest Created</option>
                      <option value="oldest">Oldest Created</option>
                      <option value="recently_updated">Recently Updated</option>
                      <option value="alphabetical">Alphabetical (A-Z)</option>
                    </select>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <label className="font-semibold text-muted-foreground uppercase tracking-wider text-[10px]">
                        Similarity Threshold
                      </label>
                      <span className="text-[10px] font-bold text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/30 px-1.5 py-0.5 rounded">
                        {(similarityThreshold * 100).toFixed(0)}%
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0.0"
                      max="1.0"
                      step="0.05"
                      value={similarityThreshold}
                      onChange={(e) => {
                        setSimilarityThreshold(parseFloat(e.target.value));
                        setOffset(0);
                      }}
                      className="w-full accent-violet-600 h-1 bg-muted rounded-lg appearance-none cursor-pointer"
                    />
                    <p className="text-[9px] text-muted-foreground/75 leading-tight">
                      Lower values show more results with lower similarity. Higher values require
                      precise match.
                    </p>
                  </div>
                )}

                {/* Source Filter */}
                <div className="space-y-1.5">
                  <label className="font-semibold text-muted-foreground uppercase tracking-wider text-[10px]">
                    Source
                  </label>
                  <select
                    value={source}
                    onChange={(e) => {
                      setSource(e.target.value);
                      setOffset(0);
                    }}
                    className="h-9 w-full rounded-md border border-input bg-background px-3 text-xs outline-none focus:ring-1 focus:ring-ring"
                  >
                    <option value="">All Sources</option>
                    {availableFilters.sources.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Entity Type Filter */}
                <div className="space-y-1.5">
                  <label className="font-semibold text-muted-foreground uppercase tracking-wider text-[10px]">
                    Entity Type
                  </label>
                  <select
                    value={entityType}
                    onChange={(e) => {
                      setEntityType(e.target.value);
                      setOffset(0);
                    }}
                    className="h-9 w-full rounded-md border border-input bg-background px-3 text-xs outline-none focus:ring-1 focus:ring-ring"
                  >
                    <option value="">All Types</option>
                    {availableFilters.entity_types.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Author Filter */}
                <div className="space-y-1.5">
                  <label className="font-semibold text-muted-foreground uppercase tracking-wider text-[10px]">
                    Author
                  </label>
                  <select
                    value={author}
                    onChange={(e) => {
                      setAuthor(e.target.value);
                      setOffset(0);
                    }}
                    className="h-9 w-full rounded-md border border-input bg-background px-3 text-xs outline-none focus:ring-1 focus:ring-ring"
                  >
                    <option value="">All Authors</option>
                    {availableFilters.authors.map((a) => (
                      <option key={a} value={a}>
                        {a}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Date range selection */}
                <div className="space-y-1.5">
                  <label className="font-semibold text-muted-foreground uppercase tracking-wider text-[10px] block">
                    Date Range
                  </label>
                  <div className="space-y-1">
                    <input
                      type="date"
                      value={dateStart}
                      onChange={(e) => {
                        setDateStart(e.target.value);
                        setOffset(0);
                      }}
                      className="h-8 w-full rounded border border-input bg-background px-2 text-[11px] outline-none"
                    />
                    <span className="text-[10px] text-muted-foreground/60 text-center block">
                      to
                    </span>
                    <input
                      type="date"
                      value={dateEnd}
                      onChange={(e) => {
                        setDateEnd(e.target.value);
                        setOffset(0);
                      }}
                      className="h-8 w-full rounded border border-input bg-background px-2 text-[11px] outline-none"
                    />
                  </div>
                </div>

                {/* Tags multi-select pills */}
                {availableFilters.tags.length > 0 && (
                  <div className="space-y-2 pt-2 border-t">
                    <label className="font-semibold text-muted-foreground uppercase tracking-wider text-[10px] block">
                      Filter by Tags
                    </label>
                    <div className="flex flex-wrap gap-1">
                      {availableFilters.tags.map((tag) => {
                        const isSelected = selectedTags.includes(tag);
                        return (
                          <button
                            key={tag}
                            type="button"
                            onClick={() => handleToggleTag(tag)}
                            className={`px-1.5 py-0.5 rounded text-[10px] font-medium border flex items-center gap-0.5 transition-all ${
                              isSelected
                                ? "bg-primary/10 border-primary text-primary"
                                : "bg-background hover:bg-muted text-muted-foreground border-border"
                            }`}
                          >
                            <Tag className="size-2 shrink-0" />
                            {tag}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Search System Status */}
            <Card className="border border-border/85 shadow-sm bg-gradient-to-b from-card to-muted/20">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/80 flex items-center gap-1.5">
                  <Database className="size-3.5 text-violet-500" /> Search System Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-[11px] pt-1">
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-muted/40 p-2 rounded-md border border-border/40">
                    <p className="text-[9px] text-muted-foreground uppercase tracking-wider">
                      Indexed Items
                    </p>
                    <p className="text-sm font-bold text-foreground">
                      {stats?.total_indexed_documents ?? 0}
                    </p>
                  </div>
                  <div className="bg-muted/40 p-2 rounded-md border border-border/40">
                    <p className="text-[9px] text-muted-foreground uppercase tracking-wider">
                      Avg Latency
                    </p>
                    <p className="text-sm font-bold text-foreground">
                      {(stats?.average_query_time_ms ?? 0).toFixed(1)} ms
                    </p>
                  </div>
                  <div className="bg-muted/40 p-2 rounded-md border border-border/40">
                    <p className="text-[9px] text-muted-foreground uppercase tracking-wider">
                      Cache Hit Rate
                    </p>
                    <p className="text-sm font-bold text-foreground">
                      {((stats?.cache_hit_rate ?? 0) * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="bg-muted/40 p-2 rounded-md border border-border/40">
                    <p className="text-[9px] text-muted-foreground uppercase tracking-wider">
                      Avg Similarity
                    </p>
                    <p className="text-sm font-bold text-foreground">
                      {((stats?.average_similarity_score ?? 0) * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                <Button
                  type="button"
                  onClick={handleReindex}
                  disabled={isReindexing}
                  variant="outline"
                  size="sm"
                  className="w-full text-xs font-medium h-8 mt-1 border-dashed hover:border-violet-500 hover:text-violet-600 transition-all flex items-center justify-center gap-1.5"
                >
                  <RefreshCw
                    className={`size-3 ${isReindexing ? "animate-spin text-violet-500" : ""}`}
                  />
                  {isReindexing ? "Reindexing..." : "Re-index All"}
                </Button>
              </CardContent>
            </Card>
          </aside>

          {/* Results Listing */}
          <main className="space-y-4 min-w-0">
            {isLoading ? (
              <div className="flex h-64 items-center justify-center">
                <RefreshCw className="size-8 animate-spin text-muted-foreground" />
              </div>
            ) : error ? (
              <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-sm text-red-700 dark:text-red-400 border border-red-200">
                {error}
              </div>
            ) : results.length === 0 ? (
              <div className="flex h-64 flex-col items-center justify-center gap-2 border border-dashed rounded-lg bg-card">
                <Database className="size-10 text-muted-foreground" />
                <p className="text-sm font-medium text-muted-foreground">
                  No search matches found.
                </p>
                <p className="text-xs text-muted-foreground/75">
                  Try adjusting filters or typing a different query.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <p>
                    Found {total} matches scoped under{" "}
                    <span className="font-semibold text-foreground">{activeProject?.name}</span>
                  </p>
                </div>

                <div className="divide-y divide-border border rounded-lg bg-card">
                  {results.map((res) => {
                    const item = res.item;
                    const score = res.score;
                    const confidence =
                      searchMode === "hybrid" ? (res as HybridSearchResult).confidence : undefined;
                    const match_type =
                      searchMode === "hybrid" ? (res as HybridSearchResult).match_type : undefined;

                    return (
                      <div
                        key={item.id}
                        onClick={() => setSelectedItemId(item.id)}
                        className={`flex flex-col gap-2 p-4 transition-colors hover:bg-muted/40 cursor-pointer ${
                          selectedItemId === item.id ? "bg-muted/50" : ""
                        }`}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-center gap-2 min-w-0">
                            {getSourceIcon(item.source, item.entity_type)}
                            <h4 className="font-semibold text-foreground leading-tight hover:underline truncate">
                              {renderHighlightedText(item.title, q)}
                            </h4>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            {/* Hybrid match type badge */}
                            {searchMode === "hybrid" && match_type && (
                              <span
                                className={`inline-flex items-center rounded-full px-2 py-0.5 text-[9px] font-bold tracking-wide uppercase ${
                                  match_type === "semantic"
                                    ? "bg-violet-50 text-violet-700 ring-1 ring-violet-700/10 dark:bg-violet-950/40 dark:text-violet-300"
                                    : match_type === "lexical"
                                      ? "bg-blue-50 text-blue-700 ring-1 ring-blue-700/10 dark:bg-blue-950/40 dark:text-blue-300"
                                      : "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-700/10 dark:bg-emerald-950/40 dark:text-emerald-300"
                                }`}
                              >
                                {match_type}
                              </span>
                            )}

                            {/* Confidence score badge */}
                            {searchMode === "hybrid" && confidence !== undefined && (
                              <span className="inline-flex items-center gap-0.5 rounded bg-violet-50 dark:bg-violet-950/30 text-violet-700 dark:text-violet-300 text-[10px] font-bold px-1.5 py-0.5 border border-violet-200 dark:border-violet-800">
                                <Sparkles className="size-2.5 text-violet-500" />
                                {Math.round(confidence * 100)}% Match
                              </span>
                            )}

                            {/* Score Metric badge */}
                            {searchMode === "standard" && score > 0 && (
                              <span className="inline-flex items-center gap-1 rounded bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-300 text-[10px] font-bold px-1.5 py-0.5 border border-green-200 dark:border-green-800">
                                <Sparkles className="size-2.5" />
                                {Math.round(score)} Relevance
                              </span>
                            )}
                            <span
                              className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${getSourceBadgeColor(
                                item.source,
                              )}`}
                            >
                              {item.source}
                            </span>
                          </div>
                        </div>

                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {renderHighlightedText(item.description, q)}
                        </p>

                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
                          {item.author && (
                            <span className="flex items-center gap-1">
                              <User className="size-3" /> {renderHighlightedText(item.author, q)}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <Calendar className="size-3" />{" "}
                            {new Date(item.updated_time).toLocaleDateString()}
                          </span>
                          {item.tags && item.tags.length > 0 && (
                            <div className="flex gap-1">
                              {item.tags.slice(0, 3).map((t: string) => (
                                <span
                                  key={t}
                                  className="inline-flex items-center gap-0.5 rounded bg-secondary px-1 py-0.5 text-[10px] text-secondary-foreground font-semibold"
                                >
                                  <Tag className="size-2" /> {renderHighlightedText(t, q)}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Pagination */}
                {total > limit && (
                  <div className="flex items-center justify-between pt-2">
                    <p className="text-xs text-muted-foreground">
                      Showing {offset + 1} to {Math.min(offset + limit, total)} of {total} results
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setOffset(Math.max(0, offset - limit))}
                        disabled={offset === 0}
                      >
                        <ChevronLeft className="size-4 mr-1" /> Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setOffset(offset + limit)}
                        disabled={offset + limit >= total}
                      >
                        Next <ChevronRight className="size-4 ml-1" />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </main>

          {/* Details Drawer */}
          <aside className="space-y-6">
            <Card className="h-[calc(100vh-240px)] overflow-y-auto sticky top-6">
              <CardHeader className="pb-3 border-b">
                <CardTitle className="text-base font-semibold">Entity Details</CardTitle>
                <CardDescription className="text-xs">
                  Review parameters, body content, and navigable relationships.
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4 space-y-6">
                {!selectedItemId ? (
                  <div className="flex h-64 flex-col items-center justify-center gap-2 text-center text-muted-foreground">
                    <Database className="size-8" />
                    <p className="text-xs font-semibold">No selection.</p>
                    <p className="text-[10px] text-muted-foreground/60 max-w-[200px]">
                      Click a search result card to examine attributes & relationship graphs.
                    </p>
                  </div>
                ) : isDetailLoading ? (
                  <div className="flex h-64 items-center justify-center">
                    <RefreshCw className="size-6 animate-spin text-muted-foreground" />
                  </div>
                ) : detailError || !selectedItem ? (
                  <div className="rounded-md bg-red-50 p-3 text-xs text-red-700 ring-1 ring-red-700/10">
                    {detailError || "Failed to retrieve drawer info."}
                  </div>
                ) : (
                  <div className="space-y-5 text-xs">
                    <div>
                      <div className="flex items-center gap-1.5 mb-2">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[9px] font-semibold ring-1 ring-inset ${getSourceBadgeColor(
                            selectedItem.source,
                          )}`}
                        >
                          {selectedItem.source}
                        </span>
                        <span className="inline-flex items-center rounded-full bg-secondary text-secondary-foreground text-[9px] font-semibold px-2 py-0.5 capitalize">
                          {selectedItem.entity_type}
                        </span>
                      </div>
                      <h3 className="font-semibold text-foreground text-sm leading-snug">
                        {selectedItem.title}
                      </h3>
                      {selectedItem.url && (
                        <a
                          href={selectedItem.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-2 inline-flex items-center text-[10px] text-primary hover:underline gap-0.5 font-bold"
                        >
                          View Original Document <ExternalLink className="size-3" />
                        </a>
                      )}
                    </div>

                    <div className="space-y-2 pt-3 border-t border-border">
                      <h4 className="font-semibold text-muted-foreground uppercase tracking-wider text-[9px]">
                        Properties
                      </h4>
                      <div className="space-y-1.5">
                        {selectedItem.author && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Author:</span>
                            <span className="font-medium text-foreground">
                              {selectedItem.author}
                            </span>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Created:</span>
                          <span className="font-medium text-foreground">
                            {new Date(selectedItem.created_time).toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Updated:</span>
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
                      <div className="space-y-1.5 pt-3 border-t border-border">
                        <h4 className="font-semibold text-muted-foreground uppercase tracking-wider text-[9px]">
                          Description
                        </h4>
                        <p className="text-[11px] text-foreground bg-muted p-2 rounded leading-normal whitespace-pre-wrap">
                          {renderHighlightedText(selectedItem.description, q)}
                        </p>
                      </div>
                    )}

                    {selectedItem.content && (
                      <div className="space-y-1.5 pt-3 border-t border-border">
                        <h4 className="font-semibold text-muted-foreground uppercase tracking-wider text-[9px]">
                          Content Body
                        </h4>
                        <div className="max-h-48 overflow-y-auto text-[11px] text-foreground bg-muted p-2 rounded font-mono leading-normal whitespace-pre-wrap">
                          {renderHighlightedText(selectedItem.content, q)}
                        </div>
                      </div>
                    )}

                    {/* Search Explanation Breakdown (Hybrid mode only) */}
                    {searchMode === "hybrid" &&
                      selectedItemId &&
                      (() => {
                        const currentRes = results.find((r) => r.item.id === selectedItemId) as
                          | HybridSearchResult
                          | undefined;
                        if (!currentRes || !currentRes.explanation) return null;
                        const exp = currentRes.explanation;
                        return (
                          <div className="space-y-2 pt-3 border-t border-border">
                            <h4 className="font-semibold text-muted-foreground uppercase tracking-wider text-[9px] flex items-center gap-1">
                              <Sparkles className="size-3 text-violet-500" /> AI Retrieval
                              Explanation
                            </h4>
                            <div className="space-y-2 bg-violet-50/30 dark:bg-violet-950/10 p-2.5 rounded-lg border border-violet-100 dark:border-violet-900/40">
                              <div className="grid grid-cols-2 gap-2 text-[10px]">
                                <div>
                                  <span className="text-muted-foreground block text-[9px]">
                                    Lexical Score
                                  </span>
                                  <span className="font-semibold text-foreground">
                                    {exp.lexical_score?.toFixed(1) ?? "0.0"}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground block text-[9px]">
                                    Semantic Similarity
                                  </span>
                                  <span className="font-semibold text-foreground">
                                    {exp.semantic_score !== undefined
                                      ? `${(exp.semantic_score * 100).toFixed(0)}%`
                                      : "N/A"}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground block text-[9px]">
                                    RRF Rank Score
                                  </span>
                                  <span className="font-semibold text-foreground">
                                    {exp.final_rank?.toFixed(4) ?? "N/A"}
                                  </span>
                                </div>
                              </div>

                              {exp.matching_fields && exp.matching_fields.length > 0 && (
                                <div className="pt-1.5 border-t border-border/40">
                                  <span className="text-muted-foreground text-[9px] block mb-1">
                                    Matching Fields
                                  </span>
                                  <div className="flex flex-wrap gap-1">
                                    {exp.matching_fields.map((f: string) => (
                                      <span
                                        key={f}
                                        className="text-[8px] font-bold px-1.5 py-0.5 rounded bg-secondary uppercase text-foreground"
                                      >
                                        {f}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {exp.reasons && exp.reasons.length > 0 && (
                                <div className="pt-1.5 border-t border-border/40">
                                  <span className="text-muted-foreground text-[9px] block mb-1">
                                    Reasoning Breakdown
                                  </span>
                                  <ul className="list-disc pl-3.5 space-y-0.5 text-[10px] text-muted-foreground">
                                    {exp.reasons.map((r: string, idx: number) => (
                                      <li key={idx}>{r}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })()}

                    {/* Relationships Graph mapping */}
                    <div className="space-y-2 pt-3 border-t border-border">
                      <h4 className="font-semibold text-muted-foreground uppercase tracking-wider text-[9px] flex items-center gap-1">
                        <Link2 className="size-3" /> Related Elements ({relationships.length})
                      </h4>
                      {relationships.length === 0 ? (
                        <p className="text-[10px] text-muted-foreground italic">
                          No relationship links found.
                        </p>
                      ) : (
                        <div className="space-y-1.5">
                          {relationships.map((rel) => {
                            const isSource = rel.source_item_id === selectedItem.id;
                            const related = isSource ? rel.target_item : rel.source_item;
                            if (!related) return null;

                            return (
                              <div
                                key={rel.id}
                                onClick={() => setSelectedItemId(related.id)}
                                className="flex items-center justify-between gap-2 rounded border border-border bg-card p-1.5 transition-colors hover:bg-muted cursor-pointer"
                              >
                                <div className="flex flex-col gap-0.5 min-w-0">
                                  <span className="font-semibold text-foreground truncate hover:underline">
                                    {related.title}
                                  </span>
                                  <span className="text-[9px] text-muted-foreground flex items-center gap-1">
                                    {isSource ? (
                                      <>
                                        <span>outbound</span>
                                        <ArrowRight className="size-2.5" />
                                        <span className="text-[8px] bg-primary/10 text-primary px-1 rounded font-bold uppercase">
                                          {rel.relationship_type}
                                        </span>
                                      </>
                                    ) : (
                                      <>
                                        <span>inbound</span>
                                        <ArrowRight className="size-2.5 rotate-180" />
                                        <span className="text-[8px] bg-secondary text-secondary-foreground px-1 rounded font-bold uppercase">
                                          {rel.relationship_type}
                                        </span>
                                      </>
                                    )}
                                  </span>
                                </div>
                                <span className="text-[9px] font-bold text-muted-foreground bg-secondary px-1 rounded">
                                  {Math.round(rel.confidence * 100)}%
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </DashboardLayout>
  );
}
