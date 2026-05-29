"""Hybrid retrieval + LLM answer endpoint. Implemented in Phase 4."""
from fastapi import APIRouter

router = APIRouter(prefix="/query", tags=["query"])

# POST /query -> hybrid retrieval -> LLM -> {answer, citations} (SSE stream)
