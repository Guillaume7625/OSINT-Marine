export type RoutingMode = "policy" | "manual" | "locked";

export interface Conversation {
  id: string;
  title: string;
  provider: string;
  routing_mode: RoutingMode;
  locked_model: string | null;
  manual_model: string | null;
  last_selected_model: string | null;
  total_input_tokens: number;
  total_output_tokens: number;
  total_latency_ms: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  citations?: Array<{ filename: string; chunk_index: number; page_number?: number | null }>;
}

export interface ConversationDetail {
  conversation: Conversation;
  messages: Message[];
  summary?: string | null;
}

export interface DevSettings {
  prompt_profile: {
    id: string;
    name: string;
    global_prompt: string;
    workspace_prompt: string;
    is_active: boolean;
  };
  routing_defaults: Record<string, unknown>;
}

export interface StreamEvent {
  type: string;
  delta?: string;
  provider?: string;
  model?: string;
  routing_mode?: RoutingMode;
  prompt_profile?: string;
  effective_system_prompt?: string;
  routing_rationale?: string;
  citations?: Array<{ filename: string; chunk_index: number; page_number?: number | null }>;
  error?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN;

function authHeaders(): HeadersInit {
  return API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {};
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }

  return (await response.json()) as T;
}

export const api = {
  listConversations: () => http<Conversation[]>("/api/conversations"),
  createConversation: (title: string) =>
    http<Conversation>("/api/conversations", {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  renameConversation: (conversationId: string, title: string) =>
    http<Conversation>(`/api/conversations/${conversationId}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }),
  getConversation: (conversationId: string) => http<ConversationDetail>(`/api/conversations/${conversationId}`),
  listFiles: (conversationId: string) =>
    http<Array<{ id: string; filename: string; size_bytes: number; ingestion_status: string }>>(
      `/api/conversations/${conversationId}/files`,
    ),
  uploadFile: async (conversationId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/api/conversations/${conversationId}/files`, {
      method: "POST",
      body: formData,
      headers: authHeaders(),
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    return response.json() as Promise<{ file_id: string; filename: string; chunks_created: number }>;
  },
  getDevSettings: () => http<DevSettings>("/api/settings/dev"),
  updateDevSettings: (payload: Record<string, unknown>) =>
    http<DevSettings>("/api/settings/dev", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
};

export async function streamConversation(
  conversationId: string,
  payload: {
    message: string;
    route_mode: RoutingMode;
    manual_model?: string | null;
    user_model_preference?: string | null;
    temporary_system_prompt?: string | null;
    require_tools?: boolean;
    require_rag?: boolean;
  },
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/conversations/${conversationId}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    const text = await response.text();
    throw new Error(text || "Streaming request failed");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    let separator = buffer.indexOf("\n\n");
    while (separator >= 0) {
      const rawEvent = buffer.slice(0, separator).trim();
      buffer = buffer.slice(separator + 2);

      const dataLine = rawEvent
        .split("\n")
        .map((line) => line.trim())
        .find((line) => line.startsWith("data:"));

      if (dataLine) {
        const payloadText = dataLine.slice(5).trim();
        if (payloadText) {
          onEvent(JSON.parse(payloadText) as StreamEvent);
        }
      }

      separator = buffer.indexOf("\n\n");
    }
  }
}
