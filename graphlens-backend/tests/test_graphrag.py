"""Phase 3 tests — exercise the logic around GraphRAG without installing it
or making any LLM calls (the index/query boundary is mocked)."""
import pytest

from models.retrieval import RetrievedChunk
from services import graphrag_index, graphrag_query, hybrid


# ── corpus export ──────────────────────────────────────────────────
def test_add_document_writes_corpus_file(tmp_path, monkeypatch):
    monkeypatch.setattr("config.settings.graphrag_root", str(tmp_path / "ws"))
    name = graphrag_index.add_document("samples/sample.pdf")
    assert name == "sample.txt"
    written = (tmp_path / "ws" / "input" / "sample.txt").read_text(encoding="utf-8")
    assert "Acme Robotics" in written  # extracted real text


# ── CLI output cleaning ────────────────────────────────────────────
def test_clean_strips_success_banner():
    raw = "SUCCESS: Local Search Response:\nDr. Voss used to work at Initech."
    assert graphrag_query._clean(raw) == "Dr. Voss used to work at Initech."


def test_query_requires_index(monkeypatch):
    monkeypatch.setattr(graphrag_query, "is_indexed", lambda: False)
    with pytest.raises(RuntimeError):
        graphrag_query.local_search("anything")


def test_invalid_method_rejected(monkeypatch):
    monkeypatch.setattr(graphrag_query, "is_indexed", lambda: True)
    with pytest.raises(ValueError):
        graphrag_query._query("sideways", "q")


# ── hybrid retrieval ───────────────────────────────────────────────
def _fake_chunk():
    return RetrievedChunk(chunk_id="c1", score=0.9, doc_id="d1",
                          filename="f.pdf", page=1, chunk_text="vector hit")


def test_hybrid_vector_only(monkeypatch):
    monkeypatch.setattr("services.vectorstore.search",
                        lambda *a, **k: [_fake_chunk()])
    ctx = hybrid.hybrid_retrieve("q", user_id="alice", use_graph=False)
    assert ctx.graph_answer is None
    assert len(ctx.vector_chunks) == 1
    assert ctx.vector_chunks[0].chunk_text == "vector hit"


def test_hybrid_combines_graph_and_vector(monkeypatch):
    monkeypatch.setattr("services.vectorstore.search",
                        lambda *a, **k: [_fake_chunk()])
    monkeypatch.setattr("services.graphrag_query.local_search",
                        lambda q: "graph reasoning answer")
    ctx = hybrid.hybrid_retrieve("q", user_id="alice", use_graph=True)
    assert ctx.graph_answer == "graph reasoning answer"
    assert ctx.graph_method == "local"
    assert len(ctx.vector_chunks) == 1


def test_hybrid_degrades_when_graph_errors(monkeypatch):
    monkeypatch.setattr("services.vectorstore.search",
                        lambda *a, **k: [_fake_chunk()])
    def boom(q):
        raise RuntimeError("no index")
    monkeypatch.setattr("services.graphrag_query.local_search", boom)
    ctx = hybrid.hybrid_retrieve("q", user_id="alice", use_graph=True)
    assert ctx.graph_answer is None          # degraded gracefully
    assert len(ctx.vector_chunks) == 1       # vector side still works
