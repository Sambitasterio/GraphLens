"""OpenAI embedding wrapper, batched to stay under request limits.

The client is created lazily so importing this module never requires an
API key (tests can monkeypatch `embed_texts` or set a fake key).
"""
from __future__ import annotations

from functools import lru_cache

from config import settings

# OpenAI allows up to 2048 inputs/request; keep a safe margin.
_BATCH_SIZE = 128


@lru_cache
def _client():
    from openai import OpenAI

    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set — required to create embeddings."
        )
    return OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: list[str], batch_size: int = _BATCH_SIZE) -> list[list[float]]:
    """Embed a list of strings, preserving input order."""
    if not texts:
        return []
    client = _client()
    vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
            dimensions=settings.embedding_dimensions,
        )
        vectors.extend(item.embedding for item in resp.data)
    return vectors
