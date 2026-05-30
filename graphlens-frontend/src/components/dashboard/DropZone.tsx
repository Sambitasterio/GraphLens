"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { toast } from "sonner";
import { UploadCloud } from "lucide-react";

import { errorMessage } from "@/lib/auth";
import { uploadDocument } from "@/lib/documents";

export function DropZone({ onUploaded }: { onUploaded: () => void }) {
  const [busy, setBusy] = useState(false);

  const onDrop = useCallback(
    async (files: File[]) => {
      const file = files[0];
      if (!file) return;
      setBusy(true);
      try {
        await uploadDocument(file);
        toast.success(`Uploading "${file.name}" — processing…`);
        onUploaded();
      } catch (err) {
        toast.error(errorMessage(err, "Upload failed"));
      } finally {
        setBusy(false);
      }
    },
    [onUploaded],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    disabled: busy,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
  });

  return (
    <div
      {...getRootProps()}
      className={`glass-soft flex cursor-pointer flex-col items-center justify-center gap-2 rounded-[16px] border-2 border-dashed px-4 py-8 text-center transition-colors ${
        isDragActive ? "border-[#0084ff] bg-[#0084ff]/5" : "border-black/15"
      } ${busy ? "opacity-60" : ""}`}
    >
      <input {...getInputProps()} />
      <UploadCloud className="h-7 w-7 text-[#0084ff]" />
      <p className="text-sm font-medium text-black/70">
        {busy
          ? "Uploading…"
          : isDragActive
            ? "Drop the file here"
            : "Drag a file or click to upload"}
      </p>
      <p className="text-xs text-black/40">PDF, Word, or Excel · up to 10MB</p>
    </div>
  );
}
