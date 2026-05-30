"use client";

import { Quote } from "lucide-react";
import type { Citation } from "@/lib/query";

export function CitationPanel({ citations }: { citations: Citation[] }) {
  return (
    <div className="flex h-full flex-col">
      <h2 className="mb-3 flex items-center gap-2 font-heading text-sm font-bold text-black/70">
        <Quote className="h-4 w-4 text-[#0084ff]" />
        Sources
      </h2>

      {citations.length === 0 ? (
        <p className="text-sm text-black/40">
          Citations for the latest answer will appear here.
        </p>
      ) : (
        <ul className="space-y-3">
          {citations.map((c, i) => (
            <li key={c.chunk_id} className="glass-soft rounded-[12px] p-3">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs font-semibold text-[#0084ff]">
                  [{i + 1}] {c.filename ?? "source"}
                </span>
                {c.page != null && (
                  <span className="text-[10px] text-black/40">p.{c.page}</span>
                )}
              </div>
              <p className="line-clamp-5 text-xs leading-relaxed text-black/60">
                {c.text}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
