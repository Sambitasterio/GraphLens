import { api } from "./api";

export interface DocumentItem {
  id: string;
  filename: string;
  status: "processing" | "ready" | "failed";
  chunk_count: number;
  uploaded_at: string;
  error?: string | null;
  owned: boolean;
}

export async function listDocuments(): Promise<DocumentItem[]> {
  const { data } = await api.get<DocumentItem[]>("/documents");
  return data;
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<DocumentItem>("/documents/upload", form);
  return data;
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`);
}

export async function shareDocument(id: string, email: string): Promise<void> {
  await api.post(`/documents/${id}/share`, { user_email: email });
}
