"""Query endpoint: hybrid retrieval -> LLM -> answer + citations.

`POST /query`        -> JSON {answer, citations}
`POST /query/stream` -> Server-Sent Events: token deltas, then a citations
                        event, then [DONE].
`GET  /query/history`-> recent logged queries for the current user.

Every query is recorded to the query_logs table (Phase 5).
"""
# No `from __future__ import annotations` — it turns `req: QueryRequest` into a
# ForwardRef that FastAPI mis-reads as a query param instead of a JSON body.
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db import SessionLocal, get_db
from models.db_models import QueryLog, User
from models.schemas import QueryLogOut, QueryRequest, QueryResponse
from services import access, hybrid, llm, querylog
from services.llm import LLMResult
from services.ratelimit import limiter
from services.security import get_current_user

router = APIRouter(prefix="/query", tags=["query"])


def _retrieve(req: QueryRequest, user: User, db):
    # RBAC: restrict vector retrieval to docs the user owns or was granted.
    # accessible_doc_ids returns None for admins (unrestricted), [] for a user
    # with no docs (→ no vector hits), or a list of allowed doc ids.
    doc_ids = access.accessible_doc_ids(db, user)
    return hybrid.hybrid_retrieve(
        req.query,
        doc_ids=doc_ids,
        top_k=req.top_k,
        use_graph=req.use_graph,
        graph_method=req.graph_method,
    )


@router.post("", response_model=QueryResponse)
@limiter.limit("30/minute")
def query(
    request: Request,
    req: QueryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ctx = _retrieve(req, user, db)
    result = llm.generate_answer(ctx)
    citations = llm.citations_from(ctx)
    querylog.record_query(
        db, user_id=user.id, req=req, ctx=ctx, result=result, citations=citations
    )
    return QueryResponse(answer=result.answer, citations=citations)


@router.post("/stream")
@limiter.limit("30/minute")
def query_stream(
    request: Request,
    req: QueryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ctx = _retrieve(req, user, db)
    citations = llm.citations_from(ctx)
    collected: dict = {"text": "", "result": None}

    def _on_complete(res: LLMResult) -> None:
        collected["result"] = res

    def event_stream():
        for token in llm.stream_answer(ctx, on_complete=_on_complete):
            collected["text"] += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        yield f"data: {json.dumps({'citations': [c.model_dump() for c in citations]})}\n\n"

        # Log with its own session (the request session may already be closing).
        result = collected["result"] or LLMResult(answer="")
        result.answer = collected["text"]
        log_db = SessionLocal()
        try:
            querylog.record_query(
                log_db, user_id=user.id, req=req, ctx=ctx, result=result,
                citations=citations,
            )
        finally:
            log_db.close()

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history", response_model=list[QueryLogOut])
def history(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(QueryLog)
        .filter(QueryLog.user_id == user.id)
        .order_by(QueryLog.created_at.desc())
        .limit(50)
        .all()
    )
