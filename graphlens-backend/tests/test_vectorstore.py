"""Phase 2 tests — run against an in-memory Qdrant, no server or API key.

We supply fake embeddings and an explicit query_vector so the OpenAI call
is never made; this isolates the Qdrant integration logic.
"""
import pytest

qdrant_client = pytest.importorskip("qdrant_client")
from qdrant_client import QdrantClient  # noqa: E402

from config import settings  # noqa: E402
from models.chunk import Chunk  # noqa: E402
from services import vectorstore  # noqa: E402

DIM = settings.embedding_dimensions


def _unit_vector(slot: int) -> list[float]:
    """A vector that points along a single axis (easy to match exactly)."""
    v = [0.0] * DIM
    v[slot % DIM] = 1.0
    return v


def _chunk(user_id: str, doc_id: str, text: str, slot: int) -> Chunk:
    import uuid

    return Chunk(
        chunk_id=str(uuid.uuid4()),
        doc_id=doc_id,
        user_id=user_id,
        filename=f"{doc_id}.pdf",
        page=1,
        text=text,
        token_count=len(text.split()),
        embedding=_unit_vector(slot),
    )


@pytest.fixture
def client():
    return QdrantClient(":memory:")


def test_upsert_and_search_roundtrip(client):
    chunks = [
        _chunk("alice", "doc1", "robots and warehouses", slot=0),
        _chunk("alice", "doc1", "navigation software", slot=1),
    ]
    n = vectorstore.upsert_chunks(chunks, client=client, collection="t")
    assert n == 2

    hits = vectorstore.search(
        "ignored", user_id="alice", query_vector=_unit_vector(0),
        top_k=2, client=client, collection="t",
    )
    assert hits, "expected at least one hit"
    assert hits[0].chunk_text == "robots and warehouses"  # best match for slot 0
    assert hits[0].score == pytest.approx(1.0, abs=1e-3)


def test_user_isolation(client):
    vectorstore.upsert_chunks(
        [
            _chunk("alice", "docA", "alice secret", slot=0),
            _chunk("bob", "docB", "bob secret", slot=0),
        ],
        client=client, collection="t",
    )
    hits = vectorstore.search(
        "ignored", user_id="bob", query_vector=_unit_vector(0),
        top_k=5, client=client, collection="t",
    )
    assert hits, "bob should see his own chunk"
    assert all(h.chunk_text == "bob secret" for h in hits)  # never alice's


def test_delete_by_doc(client):
    vectorstore.upsert_chunks(
        [
            _chunk("alice", "keep", "stays", slot=0),
            _chunk("alice", "drop", "goes away", slot=1),
        ],
        client=client, collection="t",
    )
    vectorstore.delete_by_doc("drop", client=client, collection="t")

    hits = vectorstore.search(
        "ignored", user_id="alice", query_vector=_unit_vector(1),
        top_k=5, client=client, collection="t",
    )
    assert all(h.doc_id != "drop" for h in hits)
