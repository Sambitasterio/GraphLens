"use client";

import { useRef, useState } from "react";
import { ArrowUp, Sparkles } from "lucide-react";

import { streamQuery, type Citation } from "@/lib/query";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function ChatWindow({
  onCitations,
}: {
  onCitations: (citations: Citation[]) => void;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [useGraph, setUseGraph] = useState(true);
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  function scrollToBottom() {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
    });
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q || streaming) return;

    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: q },
      { role: "assistant", content: "" },
    ]);
    setStreaming(true);
    onCitations([]);
    scrollToBottom();

    const appendToAssistant = (token: string) =>
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last?.role === "assistant") {
          next[next.length - 1] = { ...last, content: last.content + token };
        }
        return next;
      });

    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      setStreaming(false);
      scrollToBottom();
    };

    await streamQuery(
      { query: q, use_graph: useGraph, graph_method: "local" },
      {
        onToken: (t) => {
          appendToAssistant(t);
          scrollToBottom();
        },
        onCitations,
        onError: (msg) => {
          appendToAssistant(`⚠️ ${msg}`);
          finish();
        },
        onDone: finish,
      },
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* messages */}
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto pr-1">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center text-black/40">
            <Sparkles className="mb-3 h-8 w-8 text-[#0084ff]" />
            <p className="font-heading text-lg font-bold text-black/70">
              Ask your documents anything
            </p>
            <p className="mt-1 max-w-sm text-sm">
              Answers are grounded in your uploaded files and the knowledge
              graph, with sources cited on the right.
            </p>
          </div>
        ) : (
          messages.map((m, i) => (
            <div
              key={i}
              className={m.role === "user" ? "flex justify-end" : "flex justify-start"}
            >
              <div
                className={`max-w-[85%] whitespace-pre-wrap rounded-[14px] px-4 py-2.5 text-sm leading-relaxed ${
                  m.role === "user"
                    ? "glass-cta"
                    : "glass-soft text-black/80"
                }`}
              >
                {m.content || (
                  <span className="inline-flex gap-1">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#0084ff]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#0084ff] [animation-delay:0.15s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#0084ff] [animation-delay:0.3s]" />
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* composer */}
      <form onSubmit={handleSend} className="mt-4">
        <label className="mb-2 flex items-center gap-2 text-xs text-black/50">
          <input
            type="checkbox"
            checked={useGraph}
            onChange={(e) => setUseGraph(e.target.checked)}
            className="accent-[#0084ff]"
          />
          Use knowledge graph (multi-hop reasoning)
        </label>
        <div className="glass flex items-center gap-2 rounded-[16px] p-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your documents…"
            className="flex-1 bg-transparent px-3 py-2 text-sm outline-none placeholder:text-black/40"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim()}
            className="glass-cta flex h-9 w-9 items-center justify-center rounded-full disabled:opacity-50"
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
