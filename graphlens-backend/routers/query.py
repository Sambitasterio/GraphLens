"""Query endpoint: hybrid retrieval -> LLM -> answer + citations.

`POST /query`        -> JSON {answer, citations}
`POST /query/stream` -> Server-Sent Events: token deltas, then a citations
                        event, then [DONE].
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from models.db_models import User
from models.schemas import QueryRequest, QueryResponse
from services import hybrid, llm
from services.ratelimit import limiter
from services.security import get_current_user

router = APIRouter(prefix="/query", tags=["query"])


def _retrieve(req: QueryRequest, user: User):
    return hybrid.hybrid_retrieve(
        req.query,
        user_id=user.id,
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
):
    ctx = _retrieve(req, user)
    answer = llm.generate_answer(ctx)
    return QueryResponse(answer=answer, citations=llm.citations_from(ctx))


@router.post("/stream")
@limiter.limit("30/minute")
def query_stream(
    request: Request,
    req: QueryRequest,
    user: User = Depends(get_current_user),
):
    ctx = _retrieve(req, user)

    def event_stream():
        for token in llm.stream_answer(ctx):
            yield f"data: {json.dumps({'token': token})}\n\n"
        citations = [c.model_dump() for c in llm.citations_from(ctx)]
        yield f"data: {json.dumps({'citations': citations})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
