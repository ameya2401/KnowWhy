import React, { useState, useEffect } from "react";
import {
  Cpu,
  Brain,
  Activity,
  AlertCircle,
  FileText,
  Clock,
  Key,
  Flame,
  Send,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  queryAI,
  explainAI,
  getAIProviders,
  getAIStatistics,
} from "@/services/aiApi";
import {
  LLMProviderInfo,
  AIQueryResponse,
  AIStatisticsResponse,
} from "@/types/ai";

interface AIDebugDashboardProps {
  projectId: string;
  accessToken: string;
  isMaintainer: boolean;
}

export function AIDebugDashboard({
  projectId,
  accessToken,
  isMaintainer,
}: AIDebugDashboardProps) {
  const [providers, setProviders] = useState<LLMProviderInfo[]>([]);
  const [activeProvider, setActiveProvider] = useState<string>("openai");
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [statistics, setStatistics] = useState<AIStatisticsResponse | null>(null);

  // Form states
  const [queryText, setQueryText] = useState("");
  const [isExplainMode, setIsExplainMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Response states
  const [aiResponse, setAiResponse] = useState<AIQueryResponse | null>(null);
  const [responseTimeMs, setResponseTimeMs] = useState<number | null>(null);
  const [lastQuery, setLastQuery] = useState("");

  const loadData = async () => {
    try {
      const [provData, statsData] = await Promise.all([
        getAIProviders(accessToken),
        getAIStatistics(accessToken),
      ]);
      setProviders(provData.providers);
      setActiveProvider(provData.active_provider);
      if (!selectedProvider) {
        setSelectedProvider(provData.active_provider);
      }
      setStatistics(statsData);
    } catch (err) {
      console.error("Failed to load AI details", err);
    }
  };

  useEffect(() => {
    void loadData();
  }, [accessToken, projectId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryText.trim()) return;

    setIsLoading(true);
    setError(null);
    const start = performance.now();
    try {
      let res: AIQueryResponse;
      if (isExplainMode) {
        res = await explainAI(accessToken, projectId, queryText, selectedProvider || undefined);
      } else {
        res = await queryAI(accessToken, projectId, queryText, selectedProvider || undefined);
      }
      const duration = performance.now() - start;
      setResponseTimeMs(Math.round(duration));
      setAiResponse(res);
      setLastQuery(queryText);
      void loadData(); // Reload statistics
    } catch (err: any) {
      setError(err.message || "An error occurred during AI execution.");
      setAiResponse(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="glass-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">LLM Provider</CardTitle>
            <Cpu className="size-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {selectedProvider || activeProvider}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Active Provider: {activeProvider}
            </p>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <Activity className="size-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statistics?.total_requests ?? 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Accumulated sessions
            </p>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
            <Clock className="size-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statistics?.average_latency_ms
                ? `${Math.round(statistics.average_latency_ms)} ms`
                : "0 ms"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Context + LLM overhead
            </p>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
            <Brain className="size-4 text-pink-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statistics?.average_confidence
                ? `${Math.round(statistics.average_confidence * 100)}%`
                : "0%"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Evidence agreement factor
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        {/* Left Control Panel */}
        <div className="space-y-6">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Configuration Room</CardTitle>
              <CardDescription>
                Toggle the provider strategy and simulation mode settings.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-2">
                  LLM Provider Override
                </label>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                >
                  {providers.map((prov) => (
                    <option key={prov.id} value={prov.id}>
                      {prov.name} {!prov.is_available ? "(Simulated)" : ""}
                    </option>
                  ))}
                </select>
              </div>

              <div className="border-t border-border pt-4 space-y-2">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Provider Keys Status
                </h4>
                <div className="space-y-2">
                  {providers.map((prov) => (
                    <div key={prov.id} className="flex items-center justify-between text-sm">
                      <span className="capitalize">{prov.id} API Key</span>
                      {prov.is_available ? (
                        <span className="inline-flex items-center gap-1 rounded bg-green-50 px-1.5 py-0.5 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">
                          Configured
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded bg-yellow-50 px-1.5 py-0.5 text-xs font-medium text-yellow-700 ring-1 ring-inset ring-yellow-600/20">
                          Mocked Fallback
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Sandbox Engine */}
        <div className="space-y-6">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>RAG Sandbox Engine</CardTitle>
              <CardDescription>
                Execute context retrieval, intent parsing, and prompt reasoning without chat overhead.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="flex items-center gap-4">
                  <button
                    type="button"
                    onClick={() => setIsExplainMode(false)}
                    className={`flex-1 h-10 text-sm font-semibold rounded-md border transition-all ${
                      !isExplainMode
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-transparent text-muted-foreground border-border hover:bg-muted/50"
                    }`}
                  >
                    Standard Q&A Mode
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsExplainMode(true)}
                    className={`flex-1 h-10 text-sm font-semibold rounded-md border transition-all ${
                      isExplainMode
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-transparent text-muted-foreground border-border hover:bg-muted/50"
                    }`}
                  >
                    Concept Explanation Mode
                  </button>
                </div>

                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-2">
                    {isExplainMode ? "Concept or Entity Name" : "Your Question"}
                  </label>
                  <textarea
                    rows={3}
                    value={queryText}
                    onChange={(e) => setQueryText(e.target.value)}
                    placeholder={
                      isExplainMode
                        ? "e.g., OAuth2 authorization code flow, pgvector distance metrics"
                        : "e.g., Why did we choose OAuth2 over JWT tokens?"
                    }
                    className="w-full rounded-md border border-input bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                    required
                  />
                </div>

                <div className="flex justify-end">
                  <Button type="submit" disabled={isLoading || !queryText.trim()}>
                    {isLoading ? (
                      <>
                        <Zap className="mr-2 size-4 animate-spin" />
                        Generating Response...
                      </>
                    ) : (
                      <>
                        <Send className="mr-2 size-4" />
                        Execute RAG Pipeline
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Sandbox Response & Telemetry */}
          {error && (
            <Card className="border-red-200 bg-red-50/50">
              <CardContent className="flex items-start gap-2 p-4 text-red-700">
                <AlertCircle className="size-5 shrink-0" />
                <div>
                  <h4 className="font-semibold">Sandbox Execution Error</h4>
                  <p className="text-sm mt-1">{error}</p>
                </div>
              </CardContent>
            </Card>
          )}

          {aiResponse && (
            <div className="space-y-6">
              {/* Response telemetry metrics */}
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-lg bg-muted p-4 space-y-1">
                  <div className="text-xs text-muted-foreground">Response Latency</div>
                  <div className="text-lg font-bold flex items-center gap-1.5 text-yellow-600">
                    <Clock className="size-4" /> {responseTimeMs ?? 0} ms
                  </div>
                </div>
                <div className="rounded-lg bg-muted p-4 space-y-1">
                  <div className="text-xs text-muted-foreground">Response Confidence</div>
                  <div className="text-lg font-bold flex items-center gap-1.5 text-primary">
                    <Flame className="size-4" /> {Math.round(aiResponse.confidence_score * 100)}%
                  </div>
                </div>
                <div className="rounded-lg bg-muted p-4 space-y-1">
                  <div className="text-xs text-muted-foreground">Sources Cited</div>
                  <div className="text-lg font-bold flex items-center gap-1.5 text-green-600">
                    <FileText className="size-4" /> {aiResponse.sources.length} items
                  </div>
                </div>
              </div>

              {/* Response Answer Card */}
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle>Grounded RAG Output</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="prose dark:prose-invert max-w-none text-foreground text-sm leading-relaxed whitespace-pre-wrap">
                    {aiResponse.answer}
                  </div>

                  {/* Citations section */}
                  {aiResponse.sources.length > 0 && (
                    <div className="border-t border-border pt-4 space-y-2">
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Citations & Supporting Evidence
                      </h4>
                      <div className="space-y-2">
                        {aiResponse.sources.map((src, idx) => (
                          <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs border border-border p-2 rounded-md bg-background/50">
                            <div>
                              <span className="font-semibold text-foreground">{src.title}</span>
                              <span className="text-muted-foreground ml-2">({src.source})</span>
                            </div>
                            <div className="flex items-center gap-2">
                              {src.url && (
                                <a
                                  href={src.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-primary hover:underline font-semibold"
                                >
                                  View Source
                                </a>
                              )}
                              <span className="text-muted-foreground">
                                {new Date(src.updated_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Follow-up suggestions */}
                  {aiResponse.follow_up_suggestions.length > 0 && (
                    <div className="border-t border-border pt-4 space-y-2">
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Suggested Follow-Up Enquiries
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {aiResponse.follow_up_suggestions.map((suggestion, idx) => (
                          <button
                            key={idx}
                            onClick={() => setQueryText(suggestion)}
                            className="inline-flex items-center gap-1 rounded bg-muted px-2.5 py-1 text-xs font-medium text-foreground border border-border hover:bg-muted/80 transition-colors"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
