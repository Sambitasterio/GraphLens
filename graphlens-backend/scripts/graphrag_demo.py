"""Manual Phase 3 driver: build the shared graph and query it.

Prereqs: GraphRAG installed + workspace initialized (see
graphrag_workspace/SETUP.md), OPENAI_API_KEY/GRAPHRAG_API_KEY set.

Usage (from graphlens-backend/, venv active):
    python -m scripts.graphrag_demo build samples/sample.pdf [more.pdf ...]
    python -m scripts.graphrag_demo ask "What links Dr. Elena Voss and Initech?"
    python -m scripts.graphrag_demo ask --global "What is this corpus about?"
"""
import sys

from services import graphrag_index, graphrag_query


def _build(files: list[str]) -> int:
    if not graphrag_index.is_initialized():
        print("Workspace not initialized. See graphrag_workspace/SETUP.md")
        return 1
    for f in files:
        name = graphrag_index.add_document(f)
        print(f"  + added {name}")
    print("Indexing (this is slow and calls the LLM many times)...")
    graphrag_index.run_index()
    print("Done. Index artifacts in", graphrag_index.output_dir())
    return 0


def _ask(args: list[str]) -> int:
    use_global = "--global" in args
    query = " ".join(a for a in args if a != "--global")
    if not query:
        print('Provide a question, e.g. ask "..."')
        return 2
    answer = (
        graphrag_query.global_search(query)
        if use_global
        else graphrag_query.local_search(query)
    )
    print(f"\n[{'global' if use_global else 'local'} search]\n")
    print(answer)
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: graphrag_demo {build <files...> | ask <query>}")
        return 2
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "build":
        return _build(rest)
    if cmd == "ask":
        return _ask(rest)
    print(f"Unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
