import {
  AIQueryResponse,
  AIProvidersResponse,
  AIStatisticsResponse,
  AIConversation,
  AIModelInfo,
  AIChatRequest,
} from "@/types/ai";

const API_BASE = "http://localhost:8000/api/v1";

export async function queryAI(
  accessToken: string,
  projectId: string,
  q: string,
  provider?: string,
): Promise<AIQueryResponse> {
  const response = await fetch(`${API_BASE}/ai/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ project_id: projectId, q, provider }),
  });

  if (!response.ok) {
    throw new Error(`AI query failed: ${response.statusText}`);
  }

  return response.json() as Promise<AIQueryResponse>;
}

export async function explainAI(
  accessToken: string,
  projectId: string,
  concept: string,
  provider?: string,
): Promise<AIQueryResponse> {
  const response = await fetch(`${API_BASE}/ai/explain`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ project_id: projectId, concept, provider }),
  });

  if (!response.ok) {
    throw new Error(`AI explain failed: ${response.statusText}`);
  }

  return response.json() as Promise<AIQueryResponse>;
}

export async function getAIProviders(accessToken: string): Promise<AIProvidersResponse> {
  const response = await fetch(`${API_BASE}/ai/providers`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to load AI providers: ${response.statusText}`);
  }

  return response.json() as Promise<AIProvidersResponse>;
}

export async function getAIStatistics(accessToken: string): Promise<AIStatisticsResponse> {
  const response = await fetch(`${API_BASE}/ai/statistics`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to load AI statistics: ${response.statusText}`);
  }

  return response.json() as Promise<AIStatisticsResponse>;
}

export async function getAIModels(accessToken: string): Promise<AIModelInfo[]> {
  const response = await fetch(`${API_BASE}/ai/models`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to load AI models: ${response.statusText}`);
  }

  return response.json() as Promise<AIModelInfo[]>;
}

export async function getConversations(
  accessToken: string,
  projectId: string,
  q?: string,
): Promise<AIConversation[]> {
  const url = new URL(`${API_BASE}/ai/conversations`);
  url.searchParams.append("project_id", projectId);
  if (q) {
    url.searchParams.append("q", q);
  }

  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to load conversations: ${response.statusText}`);
  }

  return response.json() as Promise<AIConversation[]>;
}

export async function getConversation(
  accessToken: string,
  conversationId: string,
): Promise<AIConversation> {
  const response = await fetch(`${API_BASE}/ai/conversations/${conversationId}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to load conversation: ${response.statusText}`);
  }

  return response.json() as Promise<AIConversation>;
}

export async function deleteConversation(
  accessToken: string,
  conversationId: string,
): Promise<boolean> {
  const response = await fetch(`${API_BASE}/ai/conversations/${conversationId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to delete conversation: ${response.statusText}`);
  }

  const data = await response.json();
  return data.success as boolean;
}

export async function* chatStream(
  accessToken: string,
  request: AIChatRequest,
): AsyncGenerator<
  {
    token?: string;
    done?: boolean;
    conversation_id?: string;
    metadata?: Record<string, unknown>;
    error?: string;
  },
  void,
  unknown
> {
  const response = await fetch(`${API_BASE}/ai/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Chat API error: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Response body is not readable");
  }

  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) continue;

        const dataStr = trimmed.slice(6);
        try {
          const parsed = JSON.parse(dataStr);
          yield parsed;
        } catch (e) {
          console.error("Failed to parse SSE data", e);
        }
      }
    }
  } catch (err: unknown) {
    yield { error: (err as Error).message || "Streaming error" };
  }
}
