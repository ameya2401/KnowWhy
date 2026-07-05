import React, { useState, useEffect } from "react";
import {
  Brain,
  Activity,
  RefreshCw,
  Filter,
  Info,
  ExternalLink,
  ChevronRight,
  Calendar,
  CheckSquare,
  Square,
  Shield,
  AlertCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { analyzeProjectInsights, listInsights, getInsightStatistics } from "@/services/insightApi";
import type {
  EngineeringInsight,
  EngineeringInsightStatistics,
  EvidenceItem,
} from "@/types/insight";

interface EngineeringIntelligenceProps {
  projectId: string;
  accessToken: string;
  isMaintainer: boolean;
}

export function EngineeringIntelligence({
  projectId,
  accessToken,
  isMaintainer,
}: EngineeringIntelligenceProps) {
  // Data States
  const [insights, setInsights] = useState<EngineeringInsight[]>([]);
  const [statistics, setStatistics] = useState<EngineeringInsightStatistics | null>(null);
  const [selectedInsight, setSelectedInsight] = useState<EngineeringInsight | null>(null);

  // Loading & Error States
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter States
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("active");

  // Local simulated state for suggested action checkboxes
  const [completedActions, setCompletedActions] = useState<Record<string, Record<number, boolean>>>(
    {},
  );

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const insightsData = await listInsights(accessToken, projectId, {
        status: statusFilter === "all" ? undefined : statusFilter,
        severity: severityFilter === "all" ? undefined : severityFilter,
        insight_type: typeFilter === "all" ? undefined : typeFilter,
      });
      const statsData = await getInsightStatistics(accessToken, projectId);

      setInsights(insightsData);
      setStatistics(statsData);

      // Auto-select first insight if available and none selected
      if (insightsData.length > 0) {
        setSelectedInsight(insightsData[0]);
      } else {
        setSelectedInsight(null);
      }
    } catch (err: unknown) {
      console.error("Failed to load insights data", err);
      setError(
        (err as Error)?.message ||
          "Failed to load Engineering Intelligence insights. Please ensure backend services are running.",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, accessToken, severityFilter, typeFilter, statusFilter]);

  const handleRunAnalysis = async () => {
    if (analyzing) return;
    setAnalyzing(true);
    setError(null);
    try {
      await analyzeProjectInsights(accessToken, projectId);
      // Reload everything after analysis
      await loadData();
    } catch (err: unknown) {
      console.error("Analysis failed", err);
      setError(
        (err as Error)?.message || "Analysis failed. Verify LLM configuration and database state.",
      );
    } finally {
      setAnalyzing(false);
    }
  };

  const toggleActionCompleted = (insightId: string, actionIndex: number) => {
    setCompletedActions((prev) => {
      const insightActions = prev[insightId] || {};
      return {
        ...prev,
        [insightId]: {
          ...insightActions,
          [actionIndex]: !insightActions[actionIndex],
        },
      };
    });
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical":
        return "bg-red-500/10 text-red-500 border-red-500/20";
      case "warning":
        return "bg-amber-500/10 text-amber-500 border-amber-500/20";
      case "suggestion":
        return "bg-blue-500/10 text-blue-500 border-blue-500/20";
      default:
        return "bg-slate-500/10 text-slate-500 border-slate-500/20";
    }
  };

  const getSeverityBadge = (severity: string) => {
    const colorClass = getSeverityColor(severity);
    return (
      <span
        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${colorClass} uppercase tracking-wider`}
      >
        {severity}
      </span>
    );
  };

  const getInsightTypeLabel = (type: string) => {
    return type.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
  };

  const getEvidenceIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "commit":
        return <span className="w-2 h-2 rounded-full bg-indigo-500 shrink-0" />;
      case "pull_request":
        return <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />;
      case "issue":
        return <span className="w-2 h-2 rounded-full bg-amber-500 shrink-0" />;
      case "notion_page":
      case "document":
        return <span className="w-2 h-2 rounded-full bg-sky-500 shrink-0" />;
      default:
        return <span className="w-2 h-2 rounded-full bg-slate-400 shrink-0" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* HEADER ACTION CONTROLS */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Engineering Intelligence</h2>
          <p className="text-sm text-muted-foreground">
            AI-refined insights and heuristic scans analyzing knowledge gaps, design drift, and
            documentation coverage.
          </p>
        </div>
        {isMaintainer && (
          <Button
            onClick={handleRunAnalysis}
            disabled={analyzing}
            className="flex items-center gap-2 font-medium bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm"
          >
            <RefreshCw className={`size-4 ${analyzing ? "animate-spin" : ""}`} />
            {analyzing ? "Analyzing Knowledge..." : "Run Intelligence scan"}
          </Button>
        )}
      </div>

      {/* KPI METRICS ROW */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-slate-50/50 border-slate-200/60 shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Total Active Insights
            </CardDescription>
            <CardTitle className="text-3xl font-bold tracking-tight">
              {statistics?.total_insights ?? 0}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <span className="text-[10px] text-muted-foreground">Updated in real-time</span>
          </CardContent>
        </Card>

        <Card className="bg-slate-50/50 border-slate-200/60 shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Critical Severity
            </CardDescription>
            <CardTitle className="text-3xl font-bold text-red-500 tracking-tight">
              {statistics?.severity_breakdown.critical ?? 0}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <span className="text-[10px] text-muted-foreground">Requires immediate review</span>
          </CardContent>
        </Card>

        <Card className="bg-slate-50/50 border-slate-200/60 shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Warnings & Suggestions
            </CardDescription>
            <CardTitle className="text-3xl font-bold tracking-tight">
              <span className="text-amber-500">{statistics?.severity_breakdown.warning ?? 0}</span>
              <span className="text-muted-foreground mx-1.5">/</span>
              <span className="text-blue-500">
                {statistics?.severity_breakdown.suggestion ?? 0}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <span className="text-[10px] text-muted-foreground">Knowledge improvements</span>
          </CardContent>
        </Card>

        <Card className="bg-slate-50/50 border-slate-200/60 shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Avg Engine Confidence
            </CardDescription>
            <CardTitle className="text-3xl font-bold text-indigo-600 tracking-tight">
              {statistics?.average_confidence
                ? `${(statistics.average_confidence * 100).toFixed(0)}%`
                : "0%"}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="w-full bg-slate-200 rounded-full h-1.5 mt-2">
              <div
                className="bg-indigo-600 h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${(statistics?.average_confidence ?? 0) * 100}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 p-4 text-xs text-red-800 ring-1 ring-red-800/10 flex items-start gap-2.5">
          <AlertCircle className="size-4 shrink-0 mt-0.5 text-red-600" />
          <span className="leading-normal">{error}</span>
        </div>
      )}

      {/* FILTER CONTROLS ROW */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/80 p-3 rounded-lg border border-slate-100">
        <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1">
          <Filter className="size-3.5" /> Filters
        </span>

        {/* Severity filter */}
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="h-8 pl-2 pr-6 text-xs rounded-md border border-input bg-background outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="suggestion">Suggestion</option>
        </select>

        {/* Type Filter */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="h-8 pl-2 pr-6 text-xs rounded-md border border-input bg-background outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="all">All Rule Types</option>
          <option value="documentation_gap">Documentation Gaps</option>
          <option value="stale_knowledge">Stale Knowledge</option>
          <option value="architecture_drift">Architecture Drift</option>
          <option value="duplicate_knowledge">Duplicate Docs</option>
          <option value="project_health">Project Health</option>
          <option value="knowledge_coverage">Knowledge Coverage</option>
        </select>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-8 pl-2 pr-6 text-xs rounded-md border border-input bg-background outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="active">Active Only</option>
          <option value="all">All Statuses</option>
          <option value="resolved">Resolved</option>
          <option value="dismissed">Dismissed</option>
        </select>
      </div>

      {/* MAIN TWO-COLUMN DASHBOARD LAYOUT */}
      {loading ? (
        <div className="h-64 flex flex-col items-center justify-center gap-2">
          <RefreshCw className="size-8 text-indigo-600 animate-spin" />
          <span className="text-xs text-muted-foreground">Running intelligence heuristics...</span>
        </div>
      ) : insights.length === 0 ? (
        <div className="h-64 flex flex-col items-center justify-center text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50 p-6">
          <Shield className="size-10 text-muted-foreground opacity-50 mb-3" />
          <h4 className="font-semibold text-sm">No Engineering Insights Found</h4>
          <p className="text-xs text-muted-foreground max-w-sm mt-1">
            There are currently no active insights matching your filters. Try triggers a manual scan
            or modifying filters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-6 h-[580px]">
          {/* LEFT COLUMN: INSIGHTS LISTING */}
          <div className="border border-border rounded-xl bg-card overflow-hidden flex flex-col h-full shadow-xs">
            <div className="p-3 border-b border-border bg-slate-50/50">
              <span className="text-xs font-semibold text-muted-foreground">
                Active Findings ({insights.length})
              </span>
            </div>
            <div className="flex-1 overflow-y-auto divide-y divide-border">
              {insights.map((insight) => {
                const isSelected = selectedInsight?.id === insight.id;
                return (
                  <div
                    key={insight.id}
                    onClick={() => setSelectedInsight(insight)}
                    className={`p-3.5 cursor-pointer text-left transition-colors flex items-start justify-between gap-3 ${
                      isSelected
                        ? "bg-slate-50 border-l-4 border-l-indigo-600"
                        : "hover:bg-slate-50/50 border-l-4 border-l-transparent"
                    }`}
                  >
                    <div className="space-y-1.5 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        {getSeverityBadge(insight.severity)}
                        <span className="text-[10px] text-muted-foreground font-mono">
                          {getInsightTypeLabel(insight.insight_type)}
                        </span>
                      </div>
                      <h4
                        className={`text-xs font-semibold leading-tight truncate ${isSelected ? "text-indigo-600" : "text-foreground"}`}
                      >
                        {insight.title}
                      </h4>
                      <p className="text-[11px] text-muted-foreground line-clamp-2">
                        {insight.description}
                      </p>
                    </div>
                    <ChevronRight className="size-4 shrink-0 text-muted-foreground opacity-60 self-center" />
                  </div>
                );
              })}
            </div>
          </div>

          {/* RIGHT COLUMN: DETAIL INSPECTOR VIEW */}
          <div className="border border-border rounded-xl bg-card overflow-hidden flex flex-col h-full shadow-xs">
            {selectedInsight ? (
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Inspector Header */}
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 border-b border-border pb-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                      {getSeverityBadge(selectedInsight.severity)}
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-800 text-[10px] font-mono">
                        {getInsightTypeLabel(selectedInsight.insight_type)}
                      </span>
                    </div>
                    <h3 className="text-base font-bold leading-snug text-foreground">
                      {selectedInsight.title}
                    </h3>
                    <div className="flex items-center gap-3.5 text-[10px] text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Calendar className="size-3" />
                        Discovered: {new Date(selectedInsight.created_at).toLocaleDateString()}
                      </span>
                      <span>•</span>
                      <span>
                        Confidence Score: {(selectedInsight.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Description and AI refined justification */}
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Heuristic Finding
                  </h4>
                  <p className="text-xs leading-relaxed text-slate-700 bg-slate-50/70 p-3 rounded-lg border border-slate-100">
                    {selectedInsight.description}
                  </p>
                </div>

                {/* AI Refinement explainability box */}
                <div className="p-4 rounded-xl border border-indigo-100 bg-indigo-50/30 space-y-2">
                  <div className="flex items-center gap-2 text-indigo-700 font-semibold text-xs">
                    <Brain className="size-4 shrink-0 text-indigo-600" />
                    AI Reasoning & Risk Impact
                  </div>
                  <p className="text-[11px] text-indigo-900/80 leading-relaxed">
                    This insight was refined using the KnowWhy Intelligence Engine. The logic
                    detected a structural alignment issue or potential information asymmetry within
                    repository integrations. Addressing this helps limit design decay and saves
                    engineer onboarding hours.
                  </p>
                </div>

                {/* Supporting Evidence List */}
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <Activity className="size-3.5" /> Supporting Evidence
                  </h4>
                  {selectedInsight.evidence && selectedInsight.evidence.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                      {selectedInsight.evidence.map((ev: EvidenceItem, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-lg border border-slate-150 bg-slate-50/50 hover:bg-slate-50 transition-colors flex items-center justify-between gap-3 text-xs"
                        >
                          <div className="flex items-center gap-2 overflow-hidden">
                            {getEvidenceIcon(ev.entity_type)}
                            <span className="truncate font-medium text-slate-700">{ev.title}</span>
                          </div>
                          {ev.url && (
                            <a
                              href={ev.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-muted-foreground hover:text-indigo-600 shrink-0"
                            >
                              <ExternalLink className="size-3.5" />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground p-3 bg-slate-50/50 rounded-lg border border-slate-100">
                      <Info className="size-3.5" />
                      No granular items linked. Derived from aggregate database metrics.
                    </div>
                  )}
                </div>

                {/* Suggested Action Checklist */}
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Action Plan
                  </h4>
                  {selectedInsight.suggested_actions &&
                  selectedInsight.suggested_actions.length > 0 ? (
                    <div className="space-y-2">
                      {selectedInsight.suggested_actions.map((action, idx) => {
                        const isDone = completedActions[selectedInsight.id]?.[idx] || false;
                        return (
                          <div
                            key={idx}
                            onClick={() => toggleActionCompleted(selectedInsight.id, idx)}
                            className={`p-3 rounded-lg border text-xs cursor-pointer transition-all flex items-start gap-2.5 ${
                              isDone
                                ? "bg-emerald-50/30 border-emerald-200 text-slate-500 line-through"
                                : "bg-card border-slate-200 text-slate-700 hover:border-indigo-300"
                            }`}
                          >
                            <span className="shrink-0 mt-0.5">
                              {isDone ? (
                                <CheckSquare className="size-4 text-emerald-600" />
                              ) : (
                                <Square className="size-4 text-slate-400" />
                              )}
                            </span>
                            <span>{action}</span>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-xs text-muted-foreground p-3 bg-slate-50/50 rounded-lg border border-slate-100">
                      No suggested actions generated. Manual investigation recommended.
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6">
                <Info className="size-8 text-muted-foreground opacity-60 mb-2" />
                <h4 className="font-semibold text-sm">No Insight Selected</h4>
                <p className="text-xs text-muted-foreground max-w-sm mt-1">
                  Select an insight from the left panel to inspect its supporting evidence and
                  action checklists.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
