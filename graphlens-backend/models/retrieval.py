"""Result model returned by a vector-store search."""
from __future__ import annotations

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    """A chunk returned from Qdrant, with its similarity score."""

    chunk_id: str
    score: float
    doc_id: str | None = None
    filename: str | None = None
    page: int | None = None
    chunk_text: str = ""

    @classmethod
    def from_point(cls, point) -> "RetrievedChunk":
        payload = point.payload or {}
        return cls(
            chunk_id=str(point.id),
            score=point.score,
            doc_id=payload.get("doc_id"),
            filename=payload.get("filename"),
            page=payload.get("page"),
            chunk_text=payload.get("chunk_text", ""),
        )
