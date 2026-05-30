"use client";

import { useState } from "react";
import { toast } from "sonner";
import { FileText, Loader2, Share2, Trash2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { errorMessage } from "@/lib/auth";
import {
  deleteDocument,
  shareDocument,
  type DocumentItem,
} from "@/lib/documents";

const STATUS_STYLES: Record<DocumentItem["status"], string> = {
  processing: "bg-amber-100 text-amber-700",
  ready: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

export function DocumentList({
  documents,
  onChanged,
}: {
  documents: DocumentItem[];
  onChanged: () => void;
}) {
  const [shareDoc, setShareDoc] = useState<DocumentItem | null>(null);
  const [shareEmail, setShareEmail] = useState("");
  const [sharing, setSharing] = useState(false);

  async function handleDelete(doc: DocumentItem) {
    if (!confirm(`Delete "${doc.filename}"? This removes its vectors too.`)) return;
    try {
      await deleteDocument(doc.id);
      toast.success("Document deleted");
      onChanged();
    } catch (err) {
      toast.error(errorMessage(err, "Delete failed"));
    }
  }

  async function handleShare() {
    if (!shareDoc) return;
    setSharing(true);
    try {
      await shareDocument(shareDoc.id, shareEmail);
      toast.success(`Shared with ${shareEmail}`);
      setShareDoc(null);
      setShareEmail("");
    } catch (err) {
      toast.error(errorMessage(err, "Share failed"));
    } finally {
      setSharing(false);
    }
  }

  if (documents.length === 0) {
    return (
      <p className="px-1 py-6 text-center text-sm text-black/40">
        No documents yet — upload one above.
      </p>
    );
  }

  return (
    <>
      <ul className="space-y-2">
        {documents.map((doc) => (
          <li
            key={doc.id}
            className="glass-soft flex items-center gap-3 rounded-[12px] px-3 py-2.5"
          >
            <FileText className="h-4 w-4 shrink-0 text-[#0084ff]" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-black/80">
                {doc.filename}
              </p>
              <div className="mt-0.5 flex items-center gap-2">
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium ${STATUS_STYLES[doc.status]}`}
                >
                  {doc.status === "processing" && (
                    <Loader2 className="h-2.5 w-2.5 animate-spin" />
                  )}
                  {doc.status}
                </span>
                {doc.status === "ready" && (
                  <span className="text-[10px] text-black/40">
                    {doc.chunk_count} chunks
                  </span>
                )}
                {!doc.owned && (
                  <span className="text-[10px] text-black/40">shared</span>
                )}
              </div>
            </div>

            {doc.owned && (
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setShareDoc(doc)}
                  title="Share"
                  className="rounded-md p-1.5 text-black/40 hover:bg-black/5 hover:text-[#0084ff]"
                >
                  <Share2 className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(doc)}
                  title="Delete"
                  className="rounded-md p-1.5 text-black/40 hover:bg-black/5 hover:text-red-500"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>

      <Dialog
        open={shareDoc !== null}
        onOpenChange={(open) => !open && setShareDoc(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Share &ldquo;{shareDoc?.filename}&rdquo;</DialogTitle>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="share-email">User email</Label>
            <Input
              id="share-email"
              type="email"
              value={shareEmail}
              onChange={(e) => setShareEmail(e.target.value)}
              placeholder="teammate@company.com"
            />
          </div>
          <DialogFooter>
            <button
              onClick={handleShare}
              disabled={sharing || !shareEmail}
              className="glass-cta rounded-[10px] px-4 py-2 text-sm font-semibold disabled:opacity-60"
            >
              {sharing ? "Sharing…" : "Share access"}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
