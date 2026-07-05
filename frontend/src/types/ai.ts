export interface AICitation {
  knowledge_item_id: string;
  title: string;
  source: string;
  url: string | null;
  updated_at: string;
}

export interface AIQueryResponse {
  answer: string;
  confidence_score: number;
  sources: AICitation[];
  related_knowledge: string[];
  follow_up_suggestions: string[];
}

export interface LLMProviderInfo {
  id: string;
  name: string;
  is_active: boolean;
  is_available: boolean;
}

export interface AIProvidersResponse {
  providers: LLMProviderInfo[];
  active_provider: string;
}

export interface AIStatisticsResponse {
  total_requests: number;
  average_latency_ms: number;
  total_tokens_used: number;
  average_confidence: number;
}

export interface AIMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  metadata?: {
    latency_ms?: number;
    llm_latency_ms?: number;
    confidence_score?: number;
    sources?: AICitation[];
    related_knowledge?: string[];
    follow_up_suggestions?: string[];
  };
}

export interface AIConversation {
  id: string;
  project_id: string;
  user_id: string;
  title: string;
  provider: string;
  model: string | null;
  temperature: number;
  max_tokens: number;
  citation_mode: string;
  streaming_on: boolean;
  created_at: string;
  updated_at: string;
  messages: AIMessage[];
}

export interface AIModelInfo {
  provider: string;
  model_id: string;
  name: string;
  max_tokens: number;
}

export interface AIChatRequest {
  project_id: string;
  message: string;
  conversation_id?: string;
  provider?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  citation_mode?: string;
  streaming_on?: boolean;
}
