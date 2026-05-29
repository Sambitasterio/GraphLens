"""Phase 1 unit tests — run without network (embeddings disabled/mocked)."""
import pytest

from services.chunking import chunk_text, count_tokens
from services.errors import FileTooLarge, UnsupportedFileType
from services.ingestion import ingest_document, validate_upload


# ── chunking ───────────────────────────────────────────────────────
def test_short_text_is_single_chunk():
    chunks = chunk_text("a short sentence", chunk_size=512, overlap=50)
    assert chunks == ["a short sentence"]


def test_long_text_splits_with_overlap():
    text = " ".join(f"word{i}" for i in range(2000))
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    # every chunk stays within the size budget
    assert all(count_tokens(c) <= 100 for c in chunks)


def test_empty_text_yields_no_chunks():
    assert chunk_text("   ", chunk_size=100, overlap=10) == []


def test_invalid_overlap_rejected():
    with pytest.raises(ValueError):
        chunk_text("x", chunk_size=10, overlap=10)


# ── upload validation ──────────────────────────────────────────────
def test_validate_rejects_unknown_extension():
    with pytest.raises(UnsupportedFileType):
        validate_upload("malware.exe", 100)


def test_validate_rejects_oversized_file():
    with pytest.raises(FileTooLarge):
        validate_upload("big.pdf", 999 * 1024 * 1024)


# ── end-to-end on a generated .docx (no network) ───────────────────
def test_ingest_docx_produces_chunks(tmp_path):
    docx = pytest.importorskip("docx")  # python-docx
    sample = tmp_path / "sample.docx"
    document = docx.Document()
    for i in range(50):
        document.add_paragraph(f"This is paragraph number {i} with some filler text.")
    document.save(sample)

    chunks = ingest_document(sample, embed=False)

    assert chunks, "expected at least one chunk"
    assert all(c.filename == "sample.docx" for c in chunks)
    assert all(c.doc_id == chunks[0].doc_id for c in chunks)  # shared doc_id
    assert all(c.page is None for c in chunks)  # docx has no pages
    assert all(c.embedding is None for c in chunks)  # embed=False
    assert all(c.token_count > 0 for c in chunks)
