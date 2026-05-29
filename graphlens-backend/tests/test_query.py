"""Phase 4 query tests — endpoint wiring with retrieval + LLM mocked, plus
prompt-building and citation logic (no network)."""
import pytest

from models.retrieval import RetrievedChunk
from services import llm
from services.hybrid import HybridContext
from services.llm import LLMResult


# ── prompt + citation helpers ──────────────────────────────────────
def _ctx():
    return HybridContext(
        query="Who is the CTO?",
        graph_answer="Dr. Voss is the CTO.",
        graph_method="local",
        vector_chunks=[
            RetrievedChunk(chunk_id="c1", score=0.9, doc_id="d1",
                           filename="report.pdf", page=1, chunk_text="Elena Voss is CTO."),
        ],
    )


def test_build_messages_includes_graph_and_sources():
    msgs = llm.build_messages(_ctx())
    assert msgs[0]["role"] == "system"
    user = msgs[1]["content"]
    assert "Dr. Voss is the CTO." in user          # graph reasoning included
    assert "Elena Voss is CTO." in user            # vector source included
    assert "Who is the CTO?" in user               # the question


def test_citations_from_context():
    cites = llm.citations_from(_ctx())
    assert len(cites) == 1
    assert cites[0].filename == "report.pdf"
    assert cites[0].page == 1


def test_cost_estimate():
    # gpt-4o: $2.50 / 1M input, $10.00 / 1M output
    assert llm._cost("gpt-4o", 1_000_000, 1_000_000) == pytest.approx(12.5)
    assert llm._cost("unknown-model", 1000, 1000) == 0.0


# ── endpoint (retrieval + LLM mocked, auth overridden) ─────────────
@pytest.fixture
def authed_client(client, monkeypatch):
    from main import app
    from models.db_models import User
    from services.security import get_current_user

    app.dependency_overrides[get_current_user] = lambda: User(
        id="u1", email="x@y.com", hashed_password="x", role="user"
    )
    monkeypatch.setattr("services.hybrid.hybrid_retrieve", lambda *a, **k: _ctx())
    monkeypatch.setattr(
        "services.llm.generate_answer",
        lambda ctx: LLMResult(answer="Dr. Elena Voss.", total_tokens=42, cost_usd=0.001),
    )
    return client


def test_query_returns_answer_and_citations(authed_client):
    r = authed_client.post("/query", json={"query": "Who is the CTO?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"] == "Dr. Elena Voss."
    assert body["citations"][0]["filename"] == "report.pdf"


def test_query_validates_empty_query(authed_client):
    r = authed_client.post("/query", json={"query": ""})
    assert r.status_code == 422  # pydantic min_length


def test_query_is_logged_to_history(authed_client):
    authed_client.post("/query", json={"query": "Who is the CTO?"})
    r = authed_client.get("/query/history")
    assert r.status_code == 200, r.text
    logs = r.json()
    assert len(logs) == 1
    assert logs[0]["query"] == "Who is the CTO?"
    assert logs[0]["answer"] == "Dr. Elena Voss."
    assert logs[0]["total_tokens"] == 42
    assert logs[0]["citations"][0]["filename"] == "report.pdf"
