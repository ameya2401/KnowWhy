import React, { useState, useEffect, useRef } from "react";
import {
  MessageSquare,
  Send,
  Plus,
  Trash2,
  Sliders,
  Sparkles,
  Search,
  BookOpen,
  Info,
  CheckCircle,
  Clock,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  getAIModels,
  getConversations,
  getConversation,
  deleteConversation,
  chatStream,
} from "@/services/aiApi";
import { AIConversation, AIMessage, AIModelInfo, AIChatRequest } from "@/types/ai";

interface AIChatAssistantProps {
  projectId: string;
  accessToken: string;
  isMaintainer: boolean;
}

export function AIChatAssistant({ projectId, accessToken }: AIChatAssistantProps) {
  // Conversations list & active chat
  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<AIConversation | null>(null);
  const [conversationsSearch, setConversationsSearch] = useState("");
  const [models, setModels] = useState<AIModelInfo[]>([]);

  // Settings & configs
  const [selectedProvider, setSelectedProvider] = useState<string>("openai");
  const [selectedModel, setSelectedModel] = useState<string>("gpt-4o-mini");
  const [temperature, setTemperature] = useState<number>(0.7);
  const [maxTokens, setMaxTokens] = useState<number>(2000);
  const [citationMode, setCitationMode] = useState<string>("grounded");
  const [streamingOn, setStreamingOn] = useState<boolean>(true);
  const [showSettings, setShowSettings] = useState<boolean>(false);

  // Chat stream state
  const [inputMessage, setInputMessage] = useState("");
  const [streamingResponseText, setStreamingResponseText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Panel state
  const [expandedCitationMessageId, setExpandedCitationMessageId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load conversations and models on init
  const loadConversations = async (q?: string) => {
    try {
      const data = await getConversations(accessToken, projectId, q);
      setConversations(data);
    } catch (err) {
      console.error("Failed to load conversations", err);
    }
  };

  const loadModels = async () => {
    try {
      const modelList = await getAIModels(accessToken);
      setModels(modelList);
    } catch (err) {
      console.error("Failed to load models", err);
    }
  };

  useEffect(() => {
    void loadConversations();
    void loadModels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, accessToken]);

  // Handle keyword searching inside conversation logs
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      void loadConversations(conversationsSearch || undefined);
    }, 300);
    return () => clearTimeout(delayDebounce);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationsSearch]);

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeConversation?.messages, streamingResponseText, isStreaming]);

  // Select conversation
  const handleSelectConversation = async (convId: string) => {
    setError(null);
    try {
      const fullConv = await getConversation(accessToken, convId);
      setActiveConversation(fullConv);
      // Synchronize settings
      setSelectedProvider(fullConv.provider);
      if (fullConv.model) setSelectedModel(fullConv.model);
      setTemperature(fullConv.temperature);
      setMaxTokens(fullConv.max_tokens);
      setCitationMode(fullConv.citation_mode);
      setStreamingOn(fullConv.streaming_on);
    } catch {
      setError("Failed to load conversation details");
    }
  };

  // Start new conversation
  const handleNewChat = () => {
    setActiveConversation(null);
    setInputMessage("");
    setStreamingResponseText("");
    setIsStreaming(false);
    setError(null);
  };

  // Delete conversation
  const handleDeleteConversation = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat history?")) return;
    try {
      const success = await deleteConversation(accessToken, convId);
      if (success) {
        if (activeConversation?.id === convId) {
          handleNewChat();
        }
        void loadConversations(conversationsSearch || undefined);
      }
    } catch {
      alert("Failed to delete conversation");
    }
  };

  // Submit chat message
  const handleSendMessage = async (e?: React.FormEvent, directText?: string) => {
    if (e) e.preventDefault();
    const textToSend = directText || inputMessage;
    if (!textToSend.trim() || isStreaming) return;

    setInputMessage("");
    setError(null);
    setIsStreaming(true);
    setStreamingResponseText("");

    // Create prompt request payload
    const requestPayload: AIChatRequest = {
      project_id: projectId,
      message: textToSend,
      conversation_id: activeConversation?.id || undefined,
      provider: selectedProvider,
      model: selectedModel,
      temperature,
      max_tokens: maxTokens,
      citation_mode: citationMode,
      streaming_on: streamingOn,
    };

    // Optimistically update UI message list with the user message
    const tempUserMsg: AIMessage = {
      id: Math.random().toString(),
      conversation_id: activeConversation?.id || "temp",
      role: "user",
      content: textToSend,
      created_at: new Date().toISOString(),
    };

    const updatedMessages = activeConversation
      ? [...activeConversation.messages, tempUserMsg]
      : [tempUserMsg];

    setActiveConversation((prev) => {
      if (prev) {
        return { ...prev, messages: updatedMessages };
      }
      return {
        id: "temp",
        project_id: projectId,
        user_id: "",
        title: textToSend.substring(0, 40),
        provider: selectedProvider,
        model: selectedModel,
        temperature,
        max_tokens: maxTokens,
        citation_mode: citationMode,
        streaming_on: streamingOn,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages: updatedMessages,
      };
    });

    try {
      if (streamingOn) {
        const stream = chatStream(accessToken, requestPayload);
        let finalResponseReceived = false;

        for await (const chunk of stream) {
          if (chunk.error) {
            throw new Error(chunk.error);
          }
          if (chunk.token) {
            setStreamingResponseText((prev) => prev + chunk.token);
          }
          if (chunk.done) {
            finalResponseReceived = true;
            // Reload conversations to include the new one / update history
            await loadConversations(conversationsSearch || undefined);
            if (chunk.conversation_id) {
              const fullConv = await getConversation(accessToken, chunk.conversation_id);
              setActiveConversation(fullConv);
            }
            setStreamingResponseText("");
            break;
          }
        }

        if (!finalResponseReceived) {
          throw new Error("Streaming connection closed prematurely.");
        }
      } else {
        // Non-streaming response handling
        const response = await fetch("http://localhost:8000/api/v1/ai/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify(requestPayload),
        });

        if (!response.ok) {
          throw new Error(`Chat API error: ${response.statusText}`);
        }

        const data = await response.json();
        await loadConversations(conversationsSearch || undefined);
        const fullConv = await getConversation(accessToken, data.conversation_id);
        setActiveConversation(fullConv);
      }
    } catch (err: unknown) {
      setError((err as Error).message || "Something went wrong. Please check your connection.");
      // Rollback optimistic messages
      if (activeConversation?.id === "temp") {
        setActiveConversation(null);
      } else if (activeConversation) {
        setActiveConversation((prev) =>
          prev ? { ...prev, messages: prev.messages.slice(0, -1) } : null,
        );
      }
    } finally {
      setIsStreaming(false);
    }
  };

  const getSourceIcon = (source: string) => {
    switch (source.toLowerCase()) {
      case "github":
        return (
          <span className="px-1.5 py-0.5 rounded bg-gray-900 text-white font-mono text-[10px]">
            GitHub
          </span>
        );
      case "notion":
        return (
          <span className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 ring-1 ring-amber-800/10 text-[10px]">
            Notion
          </span>
        );
      case "google_drive":
        return (
          <span className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-800 ring-1 ring-blue-800/10 text-[10px]">
            GDrive
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 ring-1 ring-emerald-800/10 text-[10px]">
            Local
          </span>
        );
    }
  };

  const suggestedQuestions = [
    "What decisions have been made recently?",
    "Show comparison of available architectural designs",
    "List all project file dependencies",
    "Detail notion integrations status",
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] h-[calc(100vh-180px)] rounded-xl border border-border bg-card shadow-sm overflow-hidden">
      {/* SIDEBAR: Conversation logs history */}
      <div className="border-r border-border bg-slate-50/50 flex flex-col h-full overflow-hidden">
        <div className="p-3 border-b border-border flex flex-col gap-2">
          <Button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2"
            variant="outline"
          >
            <Plus className="size-4" /> New Chat
          </Button>

          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search chat logs..."
              value={conversationsSearch}
              onChange={(e) => setConversationsSearch(e.target.value)}
              className="w-full h-9 pl-8 pr-3 text-xs rounded-md border border-input bg-background outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
        </div>

        {/* List of chat items */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.length === 0 ? (
            <div className="text-center py-6 text-xs text-muted-foreground">
              No conversations found.
            </div>
          ) : (
            conversations.map((c) => {
              const isActive = activeConversation?.id === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => handleSelectConversation(c.id)}
                  className={`group relative flex items-center justify-between rounded-lg px-3 py-2.5 text-sm cursor-pointer transition-colors ${
                    isActive
                      ? "bg-slate-100/80 text-foreground font-medium"
                      : "text-muted-foreground hover:bg-slate-50 hover:text-foreground"
                  }`}
                >
                  <div className="flex items-center gap-2 overflow-hidden mr-6">
                    <MessageSquare className="size-4 shrink-0 opacity-70" />
                    <span className="truncate text-xs">{c.title || "Chat session"}</span>
                  </div>
                  <Button
                    onClick={(e) => handleDeleteConversation(e, c.id)}
                    variant="ghost"
                    size="icon"
                    className="absolute right-1 top-1.5 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-red-500 hover:bg-transparent h-7 w-7"
                  >
                    <Trash2 className="size-3.5" />
                  </Button>
                </div>
              );
            })
          )}
        </div>

        {/* Providers settings toggler */}
        <div className="p-3 border-t border-border bg-slate-50">
          <Button
            onClick={() => setShowSettings(!showSettings)}
            variant="ghost"
            size="sm"
            className="w-full flex items-center justify-between text-xs px-2 py-1.5 text-muted-foreground hover:text-foreground"
          >
            <span className="flex items-center gap-2 font-medium">
              <Sliders className="size-3.5" /> LLM Configurations
            </span>
            <span>{showSettings ? "Hide" : "Edit"}</span>
          </Button>
        </div>
      </div>

      {/* CHAT DISPLAY PANEL */}
      <div className="flex flex-col h-full overflow-hidden bg-background relative">
        {/* Settings view */}
        {showSettings && (
          <div className="absolute inset-x-0 top-0 bg-background/95 backdrop-blur border-b border-border z-10 p-4 shadow-sm animate-in slide-in-from-top duration-200">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1.5">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block">
                  LLM Provider
                </label>
                <select
                  value={selectedProvider}
                  onChange={(e) => {
                    setSelectedProvider(e.target.value);
                    const matchingModels = models.filter((m) => m.provider === e.target.value);
                    if (matchingModels.length > 0) {
                      setSelectedModel(matchingModels[0].model_id);
                    }
                  }}
                  className="w-full h-8 text-xs rounded-md border border-input bg-background px-2 outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="mock">Simulated Mock</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block">
                  Model Version
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full h-8 text-xs rounded-md border border-input bg-background px-2 outline-none focus:ring-1 focus:ring-ring"
                >
                  {models
                    .filter((m) => m.provider === selectedProvider)
                    .map((m) => (
                      <option key={m.model_id} value={m.model_id}>
                        {m.name}
                      </option>
                    ))}
                  {models.filter((m) => m.provider === selectedProvider).length === 0 && (
                    <option value={selectedModel}>{selectedModel}</option>
                  )}
                </select>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                    Temperature: {temperature}
                  </label>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1.2"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full h-8 cursor-pointer accent-primary"
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                    Streaming
                  </label>
                </div>
                <div className="flex items-center gap-2 h-8">
                  <input
                    type="checkbox"
                    checked={streamingOn}
                    onChange={(e) => setStreamingOn(e.target.checked)}
                    className="rounded border-input text-primary focus:ring-ring size-4 cursor-pointer"
                  />
                  <span className="text-xs text-muted-foreground">Enabled</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Message Container Area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {!activeConversation || activeConversation.messages.length === 0 ? (
            // Onboarding Welcome screen
            <div className="max-w-2xl mx-auto py-12 flex flex-col items-center justify-center text-center space-y-6">
              <div className="grid place-items-center rounded-2xl bg-indigo-50 p-4 text-indigo-600 shadow-inner">
                <Sparkles className="size-10" />
              </div>
              <div className="space-y-2">
                <h3 className="font-display text-2xl font-bold tracking-tight">
                  Welcome to KnowWhy Chat
                </h3>
                <p className="text-sm text-muted-foreground max-w-md">
                  Query organizational context files, Notion wiki docs, files from Google Drive, and
                  Git repository data directly.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-md pt-4">
                {suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(undefined, q)}
                    className="p-3 text-left rounded-xl border border-border bg-slate-50 hover:bg-slate-100/80 transition-colors text-xs text-foreground font-medium flex items-center justify-between"
                  >
                    <span>{q}</span>
                    <Plus className="size-3.5 shrink-0 ml-2 opacity-50" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            // Thread messages
            <div className="max-w-3xl mx-auto space-y-6">
              {activeConversation.messages.map((m, index) => {
                const isUser = m.role === "user";
                const sources = m.metadata?.sources || [];
                const confidence = m.metadata?.confidence_score;
                const latency = m.metadata?.latency_ms;

                return (
                  <div
                    key={m.id || index}
                    className={`flex gap-4 ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    {/* Assistant Profile picture / Avatar */}
                    {!isUser && (
                      <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-indigo-600 text-white font-semibold text-xs shadow">
                        AI
                      </div>
                    )}

                    <div className="space-y-2 max-w-[85%]">
                      <div
                        className={`rounded-2xl px-4 py-3 text-sm shadow-sm border ${
                          isUser
                            ? "bg-slate-900 border-slate-900 text-white"
                            : "bg-slate-50 border-slate-100 text-foreground"
                        }`}
                      >
                        {/* Text render */}
                        <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>

                        {/* Metrics Badge */}
                        {!isUser && (confidence !== undefined || latency !== undefined) && (
                          <div className="mt-3.5 pt-2 border-t border-slate-200/50 flex flex-wrap items-center gap-3 text-[10px] text-muted-foreground">
                            {confidence !== undefined && (
                              <span className="flex items-center gap-1">
                                <CheckCircle className="size-3 text-indigo-500" />
                                Grounded Confidence: {(confidence * 100).toFixed(0)}%
                              </span>
                            )}
                            {latency !== undefined && (
                              <span className="flex items-center gap-1">
                                <Clock className="size-3" />
                                Speed: {(latency / 1000).toFixed(2)}s
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Expandable Citations / Sources widget */}
                      {!isUser && sources.length > 0 && (
                        <div className="border border-border rounded-xl overflow-hidden bg-slate-50/50">
                          <button
                            onClick={() =>
                              setExpandedCitationMessageId(
                                expandedCitationMessageId === m.id ? null : m.id,
                              )
                            }
                            className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-muted-foreground hover:bg-slate-100/50 transition-colors"
                          >
                            <span className="flex items-center gap-1.5">
                              <BookOpen className="size-3.5" /> Sources ({sources.length})
                            </span>
                            {expandedCitationMessageId === m.id ? (
                              <ChevronUp className="size-3.5" />
                            ) : (
                              <ChevronDown className="size-3.5" />
                            )}
                          </button>
                          {expandedCitationMessageId === m.id && (
                            <div className="p-2.5 border-t border-border space-y-2 bg-background">
                              {sources.map((c, cIdx) => (
                                <div
                                  key={cIdx}
                                  className="flex items-start justify-between gap-3 p-2 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
                                >
                                  <div className="space-y-0.5">
                                    <p className="text-xs font-medium text-foreground leading-tight">
                                      {c.title}
                                    </p>
                                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                                      {getSourceIcon(c.source)}
                                      <span>•</span>
                                      <span>
                                        Updated: {new Date(c.updated_at).toLocaleDateString()}
                                      </span>
                                    </div>
                                  </div>
                                  {c.url && (
                                    <a
                                      href={c.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-muted-foreground hover:text-primary shrink-0 p-1 rounded-md hover:bg-slate-100 transition-colors"
                                    >
                                      <ExternalLink className="size-3.5" />
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* User initial avatar */}
                    {isUser && (
                      <div className="grid size-8 shrink-0 place-items-center rounded-full bg-slate-200 text-slate-700 font-bold text-xs">
                        U
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Active streaming message preview */}
              {isStreaming && streamingResponseText && (
                <div className="flex gap-4 justify-start">
                  <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-indigo-600 text-white font-semibold text-xs shadow animate-pulse">
                    AI
                  </div>
                  <div className="space-y-2 max-w-[85%]">
                    <div className="rounded-2xl px-4 py-3 text-sm shadow-sm border bg-slate-50 border-slate-100 text-foreground">
                      <div className="whitespace-pre-wrap leading-relaxed">
                        {streamingResponseText}
                        <span className="inline-block w-1.5 h-4 ml-1 bg-indigo-600 animate-bounce" />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="max-w-3xl mx-auto rounded-xl bg-red-50 p-4 text-xs text-red-800 ring-1 ring-red-800/10 flex items-start gap-2.5">
              <Info className="size-4 shrink-0 mt-0.5 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="p-4 border-t border-border bg-slate-50/50">
          <form
            onSubmit={handleSendMessage}
            className="max-w-3xl mx-auto relative flex items-center"
          >
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={isStreaming ? "Thinking..." : "Query the KnowWhy AI Engine..."}
              disabled={isStreaming}
              className="w-full h-12 pl-4 pr-12 rounded-xl border border-input bg-background text-sm outline-none focus:ring-2 focus:ring-ring disabled:opacity-70"
            />
            <Button
              type="submit"
              disabled={!inputMessage.trim() || isStreaming}
              size="icon"
              className="absolute right-1.5 top-1.5 h-9 w-9 rounded-lg"
            >
              <Send className="size-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
