import { API_URL } from "./api";
import { getToken } from "./token";

export interface Citation {
  chunk_id: string;
  filename?: string | null;
  page?: number | null;
  text: string;
}

export interface QueryBody {
  query: string;
  top_k?: number;
  use_graph?: boolean;
  graph_method?: "local" | "global";
}

interface StreamHandlers {
  onToken?: (token: string) => void;
  onCitations?: (citations: Citation[]) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
}

/**
 * Stream an answer from POST /query/stream (SSE). EventSource only supports
 * GET, so we use fetch + a ReadableStream reader and parse the `data:` frames.
 */
export async function streamQuery(
  body: QueryBody,
  handlers: StreamHandlers,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/query/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken() ?? ""}`,
      },
      body: JSON.stringify(body),
    });
  } catch {
    handlers.onError?.("Could not reach the server");
    return;
  }

  if (!res.ok || !res.body) {
    handlers.onError?.(`Request failed (${res.status})`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const line = frame.trim();
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (payload === "[DONE]") {
        handlers.onDone?.();
        continue;
      }
      try {
        const obj = JSON.parse(payload);
        if (typeof obj.token === "string") handlers.onToken?.(obj.token);
        else if (Array.isArray(obj.citations))
          handlers.onCitations?.(obj.citations);
      } catch {
        /* ignore partial / non-JSON frames */
      }
    }
  }
  handlers.onDone?.();
}
