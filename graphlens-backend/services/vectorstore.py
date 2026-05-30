"""Qdrant vector store: collection setup, upsert, filtered search, delete.

Multi-tenancy is enforced by a `user_id` payload filter on every search —
all chunks live in ONE shared collection (`graphlens_docs`), never one
collection per user/doc. Payload indexes on `user_id` and `doc_id` keep
those filters fast.

Every function takes optional `client` / `collection` overrides so tests
can run against an in-memory Qdrant (`QdrantClient(":memory:")`).
"""
from __future__ import annotations

import logging
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client import models as qm

from config import settings
from models.chunk import Chunk
from models.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


@lru_cache
def get_client() -> QdrantClient:
    """Shared client for the configured Qdrant (cloud or local Docker)."""
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )


def _client(client: QdrantClient | None) -> QdrantClient:
    return client or get_client()


def _collection(collection: str | None) -> str:
    return collection or settings.qdrant_collection


def ensure_collection(
    *, client: QdrantClient | None = None, collection: str | None = None
) -> None:
    """Create the collection + payload indexes if they don't exist. Idempotent."""
    c = _client(client)
    name = _collection(collection)

    if not c.collection_exists(name):
        c.create_collection(
            collection_name=name,
            vectors_config=qm.VectorParams(
                size=settings.embedding_dimensions,
                distance=qm.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection '%s'", name)

    # Indexes make filtered search fast; creating an existing index is a no-op.
    for field in ("user_id", "doc_id"):
        try:
            c.create_payload_index(
                collection_name=name,
                field_name=field,
                field_schema=qm.PayloadSchemaType.KEYWORD,
            )
        except Exception as exc:  # already exists / transient
            logger.debug("payload index %s: %s", field, exc)


def upsert_chunks(
    chunks: list[Chunk],
    *,
    client: QdrantClient | None = None,
    collection: str | None = None,
) -> int:
    """Upsert embedded chunks. Skips any chunk missing an embedding."""
    c = _client(client)
    name = _collection(collection)
    ensure_collection(client=c, collection=name)

    points = [
        qm.PointStruct(id=ch.chunk_id, vector=ch.embedding, payload=ch.payload())
        for ch in chunks
        if ch.embedding is not None
    ]
    if not points:
        logger.warning("upsert_chunks called with no embedded chunks")
        return 0

    c.upsert(collection_name=name, points=points, wait=True)
    logger.info("Upserted %d chunks into '%s'", len(points), name)
    return len(points)


def _build_filter(user_id: str | None, doc_ids: list[str] | None) -> qm.Filter | None:
    conditions: list[qm.FieldCondition] = []
    if user_id is not None:
        conditions.append(
            qm.FieldCondition(key="user_id", match=qm.MatchValue(value=user_id))
        )
    if doc_ids:
        conditions.append(
            qm.FieldCondition(key="doc_id", match=qm.MatchAny(any=doc_ids))
        )
    return qm.Filter(must=conditions) if conditions else None


def search(
    query: str,
    *,
    user_id: str | None = None,
    doc_ids: list[str] | None = None,
    top_k: int = 5,
    query_vector: list[float] | None = None,
    client: QdrantClient | None = None,
    collection: str | None = None,
) -> list[RetrievedChunk]:
    """Embed the query and return the top-k most similar chunks.

    Always pass `user_id` in production so a user only sees their own docs.
    `query_vector` lets callers/tests skip the OpenAI embedding call.
    """
    c = _client(client)
    name = _collection(collection)

    # An explicit empty doc_id list means "no accessible docs" → no results.
    # (Without this guard, an empty list would fall through to an unfiltered
    # search and leak everyone's chunks.)
    if doc_ids is not None and len(doc_ids) == 0:
        return []

    if query_vector is None:
        from services.embeddings import embed_texts

        query_vector = embed_texts([query])[0]

    response = c.query_points(
        collection_name=name,
        query=query_vector,
        query_filter=_build_filter(user_id, doc_ids),
        limit=top_k,
        with_payload=True,
    )
    return [RetrievedChunk.from_point(p) for p in response.points]


def delete_by_doc(
    doc_id: str,
    *,
    client: QdrantClient | None = None,
    collection: str | None = None,
) -> None:
    """Remove every chunk belonging to a document (used on doc deletion)."""
    c = _client(client)
    name = _collection(collection)
    c.delete(
        collection_name=name,
        points_selector=qm.FilterSelector(
            filter=qm.Filter(
                must=[qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id))]
            )
        ),
        wait=True,
    )
    logger.info("Deleted chunks for doc_id=%s from '%s'", doc_id, name)
