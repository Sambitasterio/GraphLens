"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { signOut, useSession } from "next-auth/react";

import { GlowBackground } from "@/components/GlowBackground";
import { ChatWindow } from "@/components/dashboard/ChatWindow";
import { CitationPanel } from "@/components/dashboard/CitationPanel";
import { DocumentList } from "@/components/dashboard/DocumentList";
import { DropZone } from "@/components/dashboard/DropZone";
import { listDocuments, type DocumentItem } from "@/lib/documents";
import type { Citation } from "@/lib/query";
import { setToken } from "@/lib/token";

export default function DashboardPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refreshDocuments = useCallback(() => {
    listDocuments().then(setDocuments).catch(() => {});
  }, []);

  // Auth gate + initial load (middleware also guards this route server-side).
  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
      return;
    }
    if (status === "authenticated" && session?.accessToken) {
      setToken(session.accessToken); // ensure token is set before we fetch
      refreshDocuments();
    }
  }, [status, session, router, refreshDocuments]);

  // Poll while any document is still processing
  useEffect(() => {
    const anyProcessing = documents.some((d) => d.status === "processing");
    if (anyProcessing && !pollRef.current) {
      pollRef.current = setInterval(refreshDocuments, 3000);
    } else if (!anyProcessing && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [documents, refreshDocuments]);

  if (status !== "authenticated" || !session?.user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white text-black/50">
        Loading…
      </div>
    );
  }

  const user = session.user;

  return (
    <div className="relative flex h-screen flex-col overflow-hidden bg-white">
      <GlowBackground />

      {/* top bar */}
      <header className="glass z-10 mx-4 mt-4 flex items-center justify-between rounded-[16px] px-6 py-3">
        <span className="font-heading text-xl font-bold">GraphLens</span>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-black/60">
            {user.email}
            {user.role === "admin" && (
              <span className="ml-2 rounded-full bg-[#0084ff]/10 px-2 py-0.5 text-xs font-medium text-[#0084ff]">
                admin
              </span>
            )}
          </span>
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="rounded-[10px] border border-black/10 px-3 py-1.5 font-medium text-black/70 transition-colors hover:bg-black/5"
          >
            Log out
          </button>
        </div>
      </header>

      {/* 3-panel workspace */}
      <main className="z-10 grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[300px_1fr_330px]">
        {/* left: upload + documents */}
        <aside className="glass flex min-h-0 flex-col gap-4 rounded-[16px] p-4">
          <DropZone onUploaded={refreshDocuments} />
          <div className="min-h-0 flex-1 overflow-y-auto">
            <DocumentList documents={documents} onChanged={refreshDocuments} />
          </div>
        </aside>

        {/* center: chat */}
        <section className="glass flex min-h-0 flex-col rounded-[16px] p-5">
          <ChatWindow onCitations={setCitations} />
        </section>

        {/* right: citations */}
        <aside className="glass hidden min-h-0 overflow-y-auto rounded-[16px] p-4 lg:block">
          <CitationPanel citations={citations} />
        </aside>
      </main>
    </div>
  );
}
