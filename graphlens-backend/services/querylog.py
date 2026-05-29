"""Persist a query + cited answer + token/cost footprint to query_logs."""
from __future__ import annotations

from sqlalchemy.orm import Session

from models.db_models import QueryLog
from models.schemas import Citation, QueryRequest
from services.hybrid import HybridContext
from services.llm import LLMResult


def record_query(
    db: Session,
    *,
    user_id: str,
    req: QueryRequest,
    ctx: HybridContext,
    result: LLMResult,
    citations: list[Citation],
) -> QueryLog:
    log = QueryLog(
        user_id=user_id,
        query=req.query,
        answer=result.answer,
        citations=[c.model_dump() for c in citations],
        used_graph=ctx.graph_answer is not None,
        graph_method=ctx.graph_method,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        total_tokens=result.total_tokens,
        cost_usd=result.cost_usd,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
