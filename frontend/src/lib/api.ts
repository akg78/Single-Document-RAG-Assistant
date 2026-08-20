import type { QueryResponse, UploadResponse } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handle<T>(res);
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_URL}/health`);
  return handle(res);
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/api/upload`, {
    method: "POST",
    body: form,
  });
  return handle(res);
}

export async function askQuestion(
  question: string,
  documentId?: string | null,
): Promise<QueryResponse> {
  return postJson<QueryResponse>("/api/query", {
    question,
    document_id: documentId || undefined,
  });
}

export async function fetchSuggestions(documentId?: string | null): Promise<string[]> {
  const data = await postJson<{ suggestions: string[] }>("/api/suggestions", {
    document_id: documentId || undefined,
    n: 4,
  });
  return data.suggestions;
}

export async function fetchTopics(documentId?: string | null): Promise<string[]> {
  const data = await postJson<{ topics: string[] }>("/api/topics", {
    document_id: documentId || undefined,
  });
  return data.topics;
}
