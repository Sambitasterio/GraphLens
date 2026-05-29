"""LLM answer generation grounded in retrieved context.

Takes a HybridContext (graph answer + vector chunks) and produces a cited
answer. Both blocking (`generate_answer`) and streaming (`stream_answer`)
variants share the same prompt.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterator

from config import settings
from models.schemas import Citation
from services.hybrid import HybridContext

SYSTEM_PROMPT = (
    "You are GraphLens, an enterprise document assistant. Answer the user's "
    "question using ONLY the provided context (knowledge-graph reasoning and "
    "source excerpts). Cite sources inline as [filename p.PAGE] when you use "
    "them. If the answer is not contained in the context, say you don't know "
    "rather than guessing."
)


@lru_cache
def _client():
    from openai import OpenAI

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set — required to generate answers.")
    return OpenAI(api_key=settings.openai_api_key)


def build_messages(ctx: HybridContext) -> list[dict]:
    parts: list[str] = []
    if ctx.graph_answer:
        parts.append(f"[Knowledge-graph reasoning]\n{ctx.graph_answer}")
    for i, chunk in enumerate(ctx.vector_chunks, start=1):
        loc = f"{chunk.filename} p.{chunk.page}" if chunk.page else f"{chunk.filename}"
        parts.append(f"[Source {i}: {loc}]\n{chunk.chunk_text}")

    context = "\n\n".join(parts) if parts else "(no context retrieved)"
    user = f"Context:\n{context}\n\nQuestion: {ctx.query}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def citations_from(ctx: HybridContext) -> list[Citation]:
    return [
        Citation(
            chunk_id=c.chunk_id, filename=c.filename, page=c.page, text=c.chunk_text
        )
        for c in ctx.vector_chunks
    ]


def generate_answer(ctx: HybridContext) -> str:
    resp = _client().chat.completions.create(
        model=settings.llm_model,
        messages=build_messages(ctx),
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


def stream_answer(ctx: HybridContext) -> Iterator[str]:
    stream = _client().chat.completions.create(
        model=settings.llm_model,
        messages=build_messages(ctx),
        temperature=0.2,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
