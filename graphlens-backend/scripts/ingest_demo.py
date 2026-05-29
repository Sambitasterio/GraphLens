"""Manual Phase 1 check: extract + chunk a real document and print results.

Usage (from graphlens-backend/, venv active):
    python -m scripts.ingest_demo path/to/file.pdf
    python -m scripts.ingest_demo path/to/file.pdf --embed   # also calls OpenAI

By default embeddings are skipped so you can verify chunking without an API
key or network. Add --embed to exercise the OpenAI call too.
"""
import argparse
import sys

from services.ingestion import ingest_document


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest a document and print its chunks.")
    parser.add_argument("file", help="Path to a .pdf, .docx, or .xlsx file")
    parser.add_argument("--embed", action="store_true", help="Also create embeddings")
    parser.add_argument("--show", type=int, default=3, help="How many chunks to preview")
    args = parser.parse_args()

    chunks = ingest_document(args.file, embed=args.embed)

    print(f"\n  File: {args.file}")
    print(f"  Total chunks: {len(chunks)}")
    if chunks:
        total_tokens = sum(c.token_count for c in chunks)
        print(f"  Total tokens: {total_tokens}")
        pages = sorted({c.page for c in chunks if c.page is not None})
        print(f"  Pages covered: {pages or 'n/a (no pages)'}")
        if args.embed:
            dim = len(chunks[0].embedding or [])
            print(f"  Embedding dim: {dim}")

    for i, chunk in enumerate(chunks[: args.show]):
        preview = chunk.text[:300].replace("\n", " ")
        print(f"\n  -- chunk {i + 1}/{len(chunks)} "
              f"(page={chunk.page}, tokens={chunk.token_count}) --")
        print(f"  {preview}{'...' if len(chunk.text) > 300 else ''}")

    return 0 if chunks else 1


if __name__ == "__main__":
    sys.exit(main())
