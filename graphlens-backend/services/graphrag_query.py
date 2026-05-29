"""Query the GraphRAG index via its CLI.

- global search: reasons over the whole graph (themes, "what is this about").
- local search: reasons over the subgraph around entities in the query
  (good for "what is the relationship between X and Y").

We shell out to `graphrag query` and clean the human-facing prefix the CLI
prints, returning just the answer text.
"""
from __future__ import annotations

import logging
import subprocess
import sys

from config import settings
from services.graphrag_index import is_indexed, workspace_root

logger = logging.getLogger(__name__)

_VALID_METHODS = {"global", "local"}


def _clean(stdout: str) -> str:
    """Strip the CLI's 'SUCCESS: ... Response:' banner, keep the answer."""
    text = stdout.strip()
    marker = "Response:"
    idx = text.find(marker)
    if idx != -1:
        text = text[idx + len(marker) :]
    return text.strip()


def _query(method: str, query: str) -> str:
    if method not in _VALID_METHODS:
        raise ValueError(f"method must be one of {_VALID_METHODS}, got {method!r}")
    if not is_indexed():
        raise RuntimeError("GraphRAG index not found — run indexing first.")

    cmd = [
        sys.executable, "-m", "graphrag", "query",
        "--root", str(workspace_root()),
        "--method", method,
        "--query", query,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
        timeout=settings.graphrag_timeout_seconds,
    )
    return _clean(result.stdout)


def global_search(query: str) -> str:
    """Whole-graph reasoning (corpus-level themes / summaries)."""
    return _query("global", query)


def local_search(query: str) -> str:
    """Entity-neighborhood reasoning (relationships, multi-hop)."""
    return _query("local", query)
