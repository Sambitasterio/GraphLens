"""LLM answer generation grounded in retrieved context.

Takes a HybridContext (graph answer + vector chunks) and produces a cited
answer. Both blocking (`generate_answer`) and streaming (`stream_answer`)
variants share the same prompt.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Iterator

from config import settings
from models.schemas import Citation
from services.hybrid import HybridContext


@dataclass
class LLMResult:
    answer: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


# Approximate OpenAI pricing in USD per 1M tokens (input, output). Update as
# pricing changes — used only for the cost estimate stored in query_logs.
_PRICING = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
}


def _cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    inp, out = _PRICING.get(model, (0.0, 0.0))
    return round(prompt_tokens / 1e6 * inp + completion_tokens / 1e6 * out, 6)


def _result(answer: str, model: str, usage) -> LLMResult:
    pt = getattr(usage, "prompt_tokens", 0) or 0
    ct = getattr(usage, "completion_tokens", 0) or 0
    tt = getattr(usage, "total_tokens", 0) or (pt + ct)
    return LLMResult(answer, pt, ct, tt, _cost(model, pt, ct))

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


def generate_answer(ctx: HybridContext) -> LLMResult:
    resp = _client().chat.completions.create(
        model=settings.llm_model,
        messages=build_messages(ctx),
        temperature=0.2,
    )
    answer = resp.choices[0].message.content or ""
    return _result(answer, settings.llm_model, resp.usage)


def stream_answer(
    ctx: HybridContext, on_complete: Callable[[LLMResult], None] | None = None
) -> Iterator[str]:
    """Yield answer tokens. When the usage chunk arrives at the end, invoke
    `on_complete` with the token/cost result (for logging)."""
    stream = _client().chat.completions.create(
        model=settings.llm_model,
        messages=build_messages(ctx),
        temperature=0.2,
        stream=True,
        stream_options={"include_usage": True},
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
        if getattr(chunk, "usage", None) and on_complete:
            on_complete(_result("", settings.llm_model, chunk.usage))
