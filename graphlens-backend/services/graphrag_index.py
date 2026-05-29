"""GraphRAG indexing over the SHARED corpus.

Per the Phase 3 decision, GraphRAG indexes a shared/admin corpus only —
per-user document privacy is handled on the Qdrant side. We drive the
GraphRAG CLI via subprocess (its CLI surface is stable across versions;
the Python API signatures are not).

Workspace layout (created by `graphrag init`):
    graphrag_workspace/
      settings.yaml      # model config (tuned for gpt-4o)
      .env               # GRAPHRAG_API_KEY=...
      input/             # <- we write corpus .txt files here
      output/            # <- generated parquet graph artifacts
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from config import settings
from services.extractors import extract_segments

logger = logging.getLogger(__name__)


def workspace_root() -> Path:
    return Path(settings.graphrag_root)


def input_dir() -> Path:
    return workspace_root() / "input"


def output_dir() -> Path:
    return workspace_root() / "output"


def is_initialized() -> bool:
    """True once `graphrag init` has produced a settings.yaml."""
    return (workspace_root() / "settings.yaml").is_file()


def is_indexed() -> bool:
    """True once an index run has produced output artifacts."""
    out = output_dir()
    return out.is_dir() and any(out.glob("*.parquet"))


def add_document(file_path: str | Path) -> str:
    """Extract a file's text and drop it into the GraphRAG input corpus.

    Returns the corpus filename written. Call this for each shared doc
    before running the index.
    """
    path = Path(file_path)
    segments = extract_segments(path)
    text = "\n\n".join(s.text for s in segments).strip()
    if not text:
        raise ValueError(f"No extractable text in {path.name}")

    input_dir().mkdir(parents=True, exist_ok=True)
    target = input_dir() / f"{path.stem}.txt"
    target.write_text(text, encoding="utf-8")
    logger.info("Added %s to GraphRAG corpus (%d chars)", target.name, len(text))
    return target.name


def run_index(check: bool = True) -> subprocess.CompletedProcess:
    """Run `graphrag index` over the workspace. Slow + paid — call deliberately."""
    if not is_initialized():
        raise RuntimeError(
            f"GraphRAG not initialized. Run: graphrag init --root {workspace_root()}"
        )
    cmd = [sys.executable, "-m", "graphrag", "index", "--root", str(workspace_root())]
    logger.info("Running GraphRAG index: %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        timeout=settings.graphrag_timeout_seconds,
    )
