import type { ApiArticle, ChatResponse, HistoryMessage } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? "/api" : "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }

  return response.json() as Promise<T>;
}

export function fetchArticles(signal?: AbortSignal): Promise<ApiArticle[]> {
  return request<ApiArticle[]>("/articles", { signal });
}

export function askQuestion(
  question: string,
  history: HistoryMessage[],
): Promise<ChatResponse> {
  return request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ question, history }),
  });
}
