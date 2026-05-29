"""Manual Phase 2 check: ingest a file, upsert to Qdrant, run a real search.

Needs the Qdrant container running (docker compose up -d qdrant) and
OPENAI_API_KEY set in .env (embeddings are real here).

Usage (from graphlens-backend/, venv active):
    python -m scripts.vectorstore_demo samples/sample.pdf "Who leads Acme?"
"""
import sys

from services.ingestion import ingest_document
from services.vectorstore import search, upsert_chunks

DEMO_USER = "demo-user"


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python -m scripts.vectorstore_demo <file> "<query>"')
        return 2
    file_path, query = sys.argv[1], sys.argv[2]

    print(f"Ingesting + embedding {file_path} ...")
    chunks = ingest_document(file_path, user_id=DEMO_USER, embed=True)
    upserted = upsert_chunks(chunks)
    print(f"Upserted {upserted} chunks to Qdrant.\n")

    print(f"Query: {query!r} (filtered to user_id={DEMO_USER})")
    hits = search(query, user_id=DEMO_USER, top_k=3)
    for i, h in enumerate(hits, 1):
        preview = h.chunk_text[:200].replace("\n", " ")
        print(f"\n  #{i}  score={h.score:.3f}  {h.filename} p.{h.page}")
        print(f"      {preview}...")
    if not hits:
        print("  (no hits — is the collection populated and the filter correct?)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
