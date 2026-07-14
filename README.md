# GraphLens — Enterprise Document Intelligence

Upload your documents and ask questions in natural language. GraphLens answers
with **cited, graph-augmented** responses — combining vector search with
Microsoft GraphRAG so it can reason *across* documents, not just match keywords.

<!-- Add a screenshot for a stronger first impression:
     save a dashboard image to docs/screenshot-dashboard.png and uncomment:
![GraphLens dashboard](docs/screenshot-dashboard.png)
-->

---

## Features

- 🔐 **Auth & RBAC** — JWT auth (FastAPI) with NextAuth httpOnly sessions; documents are private per-user and shareable.
- 📄 **Multi-format ingestion** — PDF, Word, Excel; OCR fallback for scanned PDFs.
- 🔎 **Hybrid retrieval** — Qdrant vector search + GraphRAG multi-hop reasoning, merged into one cited answer.
- 💬 **Streaming chat** — answers stream token-by-token (SSE) with a live source/citation panel.
- 🧾 **Audit trail** — every query, its citations, and token/cost are persisted to `query_logs`.
- 🎨 **Liquid-glass UI** — Next.js + Tailwind, glassmorphic design.
  

## Architecture

```
Next.js (App Router, NextAuth)
        │  REST + SSE
        ▼
FastAPI ──► Postgres   (users, documents, document_access, query_logs)
   │    ──► Qdrant      (per-user vector chunks)
   │    ──► GraphRAG    (shared knowledge graph, LanceDB)
   └──────► OpenAI      (embeddings + GPT-4o answers)
```

Document privacy is enforced on the **vector** side (retrieval is scoped to the
user's accessible `doc_id`s). The GraphRAG graph is **shared knowledge** and
answers any user; the system **degrades to vector-only** if the graph isn't
available.

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16 · React 19 · TypeScript · Tailwind v4 · shadcn/ui · NextAuth (Auth.js v5) |
| Backend | FastAPI · SQLAlchemy · Alembic · slowapi |
| Retrieval | Qdrant · Microsoft GraphRAG · OpenAI `text-embedding-3-large` |
| LLM | OpenAI GPT-4o |
| Data | PostgreSQL · Redis |
| Infra | Docker Compose · Fly.io |

## Repo layout

```
graphlens-backend/    FastAPI app (routers, services, models, alembic)
graphlens-frontend/   Next.js app (app/, components/, lib/)
docker-compose.yml    Full local stack
DEPLOY.md             Fly.io deployment guide
```

## Quick start (Docker — recommended)

```bash
# 1. backend secrets
cp graphlens-backend/.env.example graphlens-backend/.env
#    then set OPENAI_API_KEY in graphlens-backend/.env

# 2. a session secret for the frontend
export AUTH_SECRET=$(openssl rand -hex 32)

# 3. bring up the whole stack (migrations run on backend startup)
docker compose up --build
```

- Frontend → http://localhost:3000
- Backend API docs → http://localhost:8000/docs

## Local dev (without Docker)

**Backend** (Python 3.11):
```bash
cd graphlens-backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
alembic upgrade head            # needs Postgres running
uvicorn main:app --reload
```

**Frontend** (Node 20+):
```bash
cd graphlens-frontend
npm install
npm run dev
```

Postgres/Qdrant/Redis can be started alone via `docker compose up -d postgres qdrant redis`.

## GraphRAG (optional, for multi-hop answers)

```bash
cd graphlens-backend
python -m graphrag init --root graphrag_workspace   # then set gpt-4o in settings.yaml
python -m scripts.graphrag_demo build samples/sample.pdf   # paid indexing
```
See [graphrag_workspace/SETUP.md](graphlens-backend/graphrag_workspace/SETUP.md).

> ⚠️ The graph index must be built with the **same GraphRAG version** as the
> runtime (the LanceDB format is version-specific). On a mismatch, queries
> degrade to vector-only — answers still work, just without graph reasoning.

## Testing

```bash
cd graphlens-backend && source .venv/Scripts/activate
pytest -q        # offline suite — no Postgres/Qdrant/OpenAI needed
```

CI runs the suite on every push (see `.github/workflows/ci.yml`).

## Deployment

See [DEPLOY.md](DEPLOY.md) for Fly.io (backend + frontend) with managed
Postgres and Qdrant Cloud.

## License

MIT
