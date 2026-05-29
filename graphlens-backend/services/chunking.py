"""Token-based text chunking using tiktoken.

text-embedding-3-* models use the cl100k_base encoding, so we count and
split on those tokens to keep chunk sizes honest (not character counts).
"""
from __future__ import annotations

from functools import lru_cache

import tiktoken

ENCODING_NAME = "cl100k_base"
DEFAULT_CHUNK_SIZE = 512
DEFAULT_OVERLAP = 50


@lru_cache
def get_encoding() -> "tiktoken.Encoding":
    return tiktoken.get_encoding(ENCODING_NAME)


def count_tokens(text: str) -> int:
    return len(get_encoding().encode(text))


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """Split `text` into overlapping windows of ~`chunk_size` tokens.

    A non-zero overlap preserves context across chunk boundaries so a
    sentence split in two is still retrievable from either side.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    text = text.strip()
    if not text:
        return []

    enc = get_encoding()
    tokens = enc.encode(text)
    if len(tokens) <= chunk_size:
        return [text]

    step = chunk_size - overlap
    chunks: list[str] = []
    for start in range(0, len(tokens), step):
        window = tokens[start : start + chunk_size]
        chunks.append(enc.decode(window).strip())
        if start + chunk_size >= len(tokens):
            break
    return [c for c in chunks if c]
