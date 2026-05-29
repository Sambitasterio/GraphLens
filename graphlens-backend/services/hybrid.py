"""Hybrid retrieval: GraphRAG graph reasoning + Qdrant vector chunks.

Phase 3 gathers context from both sources. The final LLM synthesis (turning
this into a cited answer) lands in Phase 4 — here we just assemble the
material so it's easy to hand to the LLM.

- Vector side: per-user, always filtered by user_id (private docs).
- Graph side: the SHARED graph (no user filter); skipped gracefully if the
  graph isn't indexed yet, so the system still works vector-only.
"""
from __future__ import annotations

import logging

from models.retrieval import RetrievedChunk
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class HybridContext(BaseModel):
    query: str
    graph_answer: str | None = None
    graph_method: str | None = None
    vector_chunks: list[RetrievedChunk] = []


def hybrid_retrieve(
    query: str,
    *,
    user_id: str | None = None,
    doc_ids: list[str] | None = None,
    top_k: int = 5,
    use_graph: bool = True,
    graph_method: str = "local",
) -> HybridContext:
    from services import vectorstore

    vector_chunks = vectorstore.search(
        query, user_id=user_id, doc_ids=doc_ids, top_k=top_k
    )

    graph_answer: str | None = None
    if use_graph:
        try:
            from services import graphrag_query

            if graph_method == "global":
                graph_answer = graphrag_query.global_search(query)
            else:
                graph_answer = graphrag_query.local_search(query)
        except Exception as exc:
            # No index yet, GraphRAG not installed, etc. — degrade to vector-only.
            logger.warning("GraphRAG unavailable, using vector-only: %s", exc)
            graph_answer = None

    return HybridContext(
        query=query,
        graph_answer=graph_answer,
        graph_method=graph_method if graph_answer else None,
        vector_chunks=vector_chunks,
    )
