"""Document ingestion pipeline: validate -> extract -> chunk -> embed.

Phase 1 produces fully-formed `Chunk` objects (optionally with embeddings).
Phase 2 upserts them into Qdrant; Phase 4 wires this behind POST /upload as
an async background job. Keep this function pure/synchronous so it's easy to
enqueue and to unit-test.
"""
from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from config import settings
from models.chunk import Chunk
from services.chunking import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP,
    chunk_text,
    count_tokens,
)
from services.errors import CorruptFile, FileTooLarge, UnsupportedFileType
from services.extractors import extract_segments

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}

# Magic-byte signatures: don't trust the extension alone (Phase 0 hardening).
# .docx/.xlsx are ZIP containers, so they share the PK header.
_SIGNATURES = {
    ".pdf": [b"%PDF"],
    ".docx": [b"PK\x03\x04"],
    ".xlsx": [b"PK\x03\x04"],
}


def validate_upload(filename: str, size_bytes: int) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileType(
            f"'{ext}' is not supported. Allowed: {sorted(SUPPORTED_EXTENSIONS)}"
        )
    limit = settings.max_upload_mb * 1024 * 1024
    if size_bytes > limit:
        raise FileTooLarge(
            f"File is {size_bytes / 1e6:.1f}MB; limit is {settings.max_upload_mb}MB"
        )


def _validate_signature(path: Path) -> None:
    ext = path.suffix.lower()
    expected = _SIGNATURES.get(ext, [])
    if not expected:
        return
    with path.open("rb") as fh:
        head = fh.read(8)
    if not any(head.startswith(sig) for sig in expected):
        raise CorruptFile(
            f"Content of '{path.name}' does not match a {ext} file signature"
        )


def ingest_document(
    file_path: str | Path,
    *,
    doc_id: str | None = None,
    user_id: str | None = None,
    filename: str | None = None,
    embed: bool = True,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Turn a file on disk into a list of (optionally embedded) Chunks."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    filename = filename or path.name
    validate_upload(filename, path.stat().st_size)
    _validate_signature(path)

    doc_id = doc_id or str(uuid4())
    segments = extract_segments(path)

    chunks: list[Chunk] = []
    for segment in segments:
        for piece in chunk_text(segment.text, chunk_size, overlap):
            chunks.append(
                Chunk(
                    chunk_id=str(uuid4()),
                    doc_id=doc_id,
                    user_id=user_id,
                    filename=filename,
                    page=segment.page,
                    text=piece,
                    token_count=count_tokens(piece),
                )
            )

    logger.info("Extracted %d chunks from %s (doc_id=%s)", len(chunks), filename, doc_id)

    if embed and chunks:
        from services.embeddings import embed_texts

        vectors = embed_texts([c.text for c in chunks])
        for chunk, vector in zip(chunks, vectors):
            chunk.embedding = vector

    return chunks
