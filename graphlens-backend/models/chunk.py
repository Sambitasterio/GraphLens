"""Core data model for an ingested, embeddable document chunk."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """One retrievable unit of a document.

    `chunk_id` is a UUID string so it can be used directly as a Qdrant
    point id in Phase 2. Page is optional (PDFs have pages; Word/Excel
    don't, so it stays None and citations fall back to filename).
    """

    chunk_id: str
    doc_id: str
    user_id: str | None = None
    filename: str
    page: int | None = None
    text: str
    token_count: int
    embedding: list[float] | None = Field(default=None, repr=False)

    def payload(self) -> dict:
        """Metadata stored alongside the vector in Qdrant (Phase 2)."""
        return {
            "user_id": self.user_id,
            "doc_id": self.doc_id,
            "filename": self.filename,
            "page": self.page,
            "chunk_text": self.text,
        }
