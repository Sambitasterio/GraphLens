# GraphRAG workspace setup (Phase 3)

This folder holds the **shared/admin** GraphRAG graph. Per-user document
privacy is handled on the Qdrant side, not here.

> GraphRAG's `settings.yaml` schema changes between versions, so we let the
> tool generate the correct one and then tweak two values — rather than
> shipping a settings file that might not match your installed version.

## One-time setup (Git Bash, venv active)

```bash
cd /c/GraphLens/graphlens-backend

# 1. install GraphRAG (heavy; pulls many deps)
pip install graphrag

# 2. scaffold this workspace (creates settings.yaml, .env, prompts/, output/)
python -m graphrag init --root graphrag_workspace

# 3. put your key in the workspace .env
echo "GRAPHRAG_API_KEY=sk-...your-openai-key..." > graphrag_workspace/.env
```

## Tune the generated `settings.yaml`

Open `graphrag_workspace/settings.yaml` and set the models to match our stack
(decision: **full GPT-4o quality**, embeddings aligned with Qdrant):

- chat model  → `gpt-4o`
- embedding model → `text-embedding-3-large`

In current GraphRAG (2.x) these live under a `models:` block, e.g.:

```yaml
models:
  default_chat_model:
    type: openai_chat
    model: gpt-4o
    api_key: ${GRAPHRAG_API_KEY}
  default_embedding_model:
    type: openai_embedding
    model: text-embedding-3-large
    api_key: ${GRAPHRAG_API_KEY}
```

(Older 1.x layouts use top-level `llm:` / `embeddings:` blocks — set the same
two model names there instead.)

## Build + query (driven from our code)

```bash
# add shared docs to the corpus, then index (slow + paid)
python -m scripts.graphrag_demo build samples/sample.pdf

# ask a multi-hop question once indexing finishes
python -m scripts.graphrag_demo ask "What is the relationship between Dr. Elena Voss and Initech?"
```
