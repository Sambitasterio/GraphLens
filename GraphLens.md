# GraphLens — Enterprise Document Intelligence Platform
> **Build Plan** | Status: ⬜ Not Started

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Document Processing** | LlamaIndex | Ingestion, chunking, indexing |
| **Graph RAG** | Microsoft GraphRAG | Graph nodes/edges, multi-hop reasoning |
| **Vector Store** | Qdrant | Semantic vector search |
| **Embeddings** | OpenAI `text-embedding-3-large` | Document + query embeddings |
| **LLM** | OpenAI GPT-4o (or Groq/local) | Answer generation, narration |
| **Backend** | FastAPI + Python | API routes, pipeline orchestration |
| **Task Queue** | Redis + RQ (or FastAPI BackgroundTasks) | Async document ingestion jobs |
| **Database** | PostgreSQL | Users, document metadata, access control |
| **Frontend** | Next.js (App Router) + TypeScript | Chat UI, drag-and-drop upload |
| **Auth** | NextAuth.js | Login, session, role management |
| **Containerization** | Docker + Docker Compose | Local dev + prod consistency |
| **Deployment** | Fly.io | Cloud hosting |
| **Env** | `.env.local` / `.env` | API keys (OpenAI, Qdrant, DB) |

---

## Phase Progress Tracker

| Phase | Description | Owner | Status | Done? |
|---|---|---|---|---|
| **0** | Environment & Repo Setup | Both | 🔄 In Progress | 50% |
| **1** | Document Ingestion Pipeline | AI | ⬜ Not Started | 0% |
| **2** | Qdrant Vector Store Setup | AI | ⬜ Not Started | 0% |
| **3** | GraphRAG Integration | AI | ⬜ Not Started | 0% |
| **4** | FastAPI Backend | AI | ⬜ Not Started | 0% |
| **5** | Citation Tracking | AI | ⬜ Not Started | 0% |
| **6** | PostgreSQL + Access Control | AI | ⬜ Not Started | 0% |
| **7** | Next.js Frontend | AI | ⬜ Not Started | 0% |
| **8** | Auth (NextAuth) | AI | ⬜ Not Started | 0% |
| **9** | Docker + Deployment | Both | ⬜ Not Started | 0% |
| **10** | Testing + Polish | Both | ⬜ Not Started | 0% |

**Status key:** ⬜ Not Started · 🔄 In Progress · ✅ Done · ❌ Blocked

---

## Agent Workflow — Pause After Every Phase

**Rule:** AI builds one phase at a time and stops. You review, confirm, then say **"continue"** or **"Phase X ready"**.

---

## Phase 0 — Environment & Repo Setup

### You (User) do:
- [ ] Create a GitHub repo named `graphlens`
- [ ] Install: Python 3.11+, Node.js 18+, Docker Desktop
- [ ] Create an OpenAI account → copy API key
- [ ] Create a Qdrant Cloud account (free tier) → copy URL + API key
- [ ] Create a PostgreSQL DB (local via Docker or Supabase free tier) → copy connection string
- [ ] Create `.env` file with placeholders:
  ```env
  OPENAI_API_KEY=
  QDRANT_URL=
  QDRANT_API_KEY=
  DATABASE_URL=
  REDIS_URL=redis://localhost:6379
  NEXTAUTH_SECRET=
  NEXTAUTH_URL=http://localhost:3000
  ```
- [ ] Run `npx create-next-app@latest graphlens-frontend --typescript --app --src-dir`
- [ ] Create `graphlens-backend/` folder for FastAPI

### AI does:
- [x] Scaffold FastAPI project structure (`main.py`, `config.py`, `routers/`, `services/`, `models/`)
- [x] Create `requirements.txt` with all Python dependencies
- [x] Create frontend dependency additions (`graphlens-frontend/FRONTEND_DEPS.md`)
- [x] Create `docker-compose.yml` (Qdrant local + PostgreSQL + Redis + backend)
- [x] Create `.env.example` (backend) + `.env.local.example` (frontend) + root `.gitignore` + backend `Dockerfile`

**Reply "Phase 0 ready" when accounts and installs are done.**

---

## Phase 1 — Document Ingestion Pipeline

### AI does:
- [ ] `services/ingestion.py` — accepts file (PDF/Word/Excel), extracts raw text
  - PDF: `pypdf` or `pdfplumber`
  - Word: `python-docx`
  - Excel: `openpyxl` / `pandas`
  - **Scanned/image PDFs:** OCR fallback via `pytesseract` / `unstructured` when extracted text is empty
- [ ] **Run ingestion as an async background job** (RQ worker or FastAPI `BackgroundTasks`) — extraction + embedding will exceed HTTP timeouts on large files
- [ ] **Upload validation:** verify true MIME type (not just extension), enforce 10MB limit server-side, reject on content sniff
- [ ] Text cleaning and chunking logic (chunk size: 512 tokens, overlap: 50)
- [ ] Embedding each chunk via `openai.embeddings.create(model="text-embedding-3-large")` (optionally pass `dimensions=1536` to halve Qdrant storage)
- [ ] Store chunk + embedding + source metadata (filename, page, chunk_id)
- [ ] Unit test (`pytest`): upload a sample PDF and assert chunk count + metadata

### You (User) do:
- [ ] Test with a real document (any PDF)
- [ ] Confirm chunks look reasonable in terminal output

**Reply "continue" when ingestion works.**

---

## Phase 2 — Qdrant Vector Store

### AI does:
- [ ] `services/vectorstore.py` — connect to Qdrant (cloud or local Docker)
- [ ] Create **single shared collection** `graphlens_docs`, vector size 3072 (or 1536 if trimmed in Phase 1). Multi-tenancy is handled via payload filtering, **not** one-collection-per-doc
- [ ] **Create payload indexes on `user_id` and `doc_id`** — filtered search degrades badly without them
- [ ] Upsert chunks with payload: `{user_id, doc_id, filename, page, chunk_text}`
- [ ] Search function: embed query → search Qdrant **with `user_id` filter** → return top-k chunks with scores
- [ ] Delete collection entries by `doc_id` (for document removal)

### You (User) do:
- [ ] Confirm Qdrant dashboard shows uploaded vectors
- [ ] Run a test query and check retrieved chunks make sense

**Reply "continue" when vector search works.**

---

## Phase 3 — GraphRAG Integration

> ⚠️ **RBAC conflict — decide before building:** GraphRAG builds ONE global graph over a corpus. Your per-user access model (Phase 6) means a shared graph would leak entities/relationships across users. Choose: (a) per-user graph indexes (correct, but indexing cost × number of users), or (b) scope GraphRAG to shared/admin docs only and keep per-user retrieval on the Qdrant side.
>
> ⚠️ **Cost/time:** GraphRAG makes many LLM calls per chunk (entity extraction + community summaries). Use `gpt-4o-mini` for the extraction steps and set a spend ceiling. Indexing even a small doc set can take 10–30 min and cost real money. Lighter alternatives if this hurts: **LightRAG** or LlamaIndex `PropertyGraphIndex` + Neo4j.

### AI does:
- [ ] Install and configure Microsoft GraphRAG (`pip install graphrag`)
- [ ] `services/graphrag_index.py` — run GraphRAG indexing on ingested text corpus (cheap model for extraction)
- [ ] Build entity/relationship graph: extract nodes (people, orgs, concepts) and edges (relationships)
- [ ] `services/graphrag_query.py` — global search (whole graph) and local search (subgraph around entity)
- [ ] Combine GraphRAG results + Qdrant vector results for hybrid retrieval

### You (User) do:
- [ ] Run GraphRAG indexing on a sample document set (takes a few minutes)
- [ ] Check `output/` folder for generated graph artifacts
- [ ] Test a multi-hop query: e.g. "What is the relationship between X and Y?"

**Reply "continue" when GraphRAG returns multi-hop answers.**

---

## Phase 4 — FastAPI Backend

### AI does:
- [ ] `routers/documents.py` — `POST /upload`, `GET /documents`, `DELETE /documents/{id}`
- [ ] `routers/query.py` — `POST /query` → runs hybrid retrieval → calls LLM → returns answer + citations (stream tokens via SSE)
- [ ] `routers/auth.py` — user login/signup endpoints (JWT tokens). **FastAPI is the single source of truth for credentials** — NextAuth (Phase 8) only delegates to these endpoints. Password hashing via `passlib[bcrypt]` (or argon2).
  - ⚠️ **Depends on the `users` table** — build the `users` table + SQLAlchemy model + Alembic setup here (pulled forward from Phase 6), since auth cannot exist without it.
- [ ] LLM call: structured prompt with retrieved chunks as context, system instruction to cite sources
- [ ] Rate limiting on `/query` and `/upload` (`slowapi`) — protects your OpenAI bill
- [ ] Response format:
  ```json
  {
    "answer": "...",
    "citations": [{"chunk_id": "...", "filename": "...", "page": 2, "text": "..."}]
  }
  ```
- [ ] CORS middleware, error handling, request validation with Pydantic

### You (User) do:
- [ ] Test all endpoints via Postman or `http://localhost:8000/docs` (FastAPI Swagger)
- [ ] Upload a doc, run a query, confirm citations appear in response

**Reply "continue" when all API routes work.**

---

## Phase 5 — Citation Tracking

### AI does:
- [ ] Every LLM response includes source chunk references
- [ ] `models/citation.py` — Citation schema: `chunk_id`, `doc_id`, `filename`, `page`, `excerpt`
- [ ] Store query + response + citations in PostgreSQL (`query_logs` table), including `tokens_used` + `cost` columns (trivial now, painful to backfill)
- [ ] API returns citations alongside answer so frontend can render them

### You (User) do:
- [ ] Verify citations point to actual text in the source document
- [ ] Check `query_logs` table in PostgreSQL has entries

**Reply "continue" when citations are tracked.**

---

## Phase 6 — PostgreSQL + Role-Based Access Control

> Note: `users` table + Alembic setup were pulled forward to Phase 4 (auth needs them). This phase adds the access-control tables on top.

### AI does:
- [ ] Tables: `users` (from Phase 4), `documents`, `document_access`, `query_logs`
- [ ] `users` — id, email, hashed_password (bcrypt/argon2), role (admin/user)
- [ ] `documents` — id, owner_id, filename, uploaded_at, **`status` (processing/ready/failed)** — no `qdrant_collection_id` since a single shared collection is used; rows are linked to vectors by `doc_id` in the Qdrant payload
- [ ] `document_access` — doc_id, user_id (many-to-many for sharing)
- [ ] All Qdrant queries filtered by `user_id` in payload — users only retrieve their own docs
- [ ] Admin can grant access: `POST /documents/{id}/share` → adds row to `document_access`
- [ ] SQLAlchemy models + Alembic migrations

### You (User) do:
- [ ] Run `alembic upgrade head` to apply migrations
- [ ] Create two test users, upload docs as user A, confirm user B cannot query them

**Reply "continue" when RBAC works.**

---

## Phase 7 — Next.js Frontend

### AI does:
- [ ] `app/page.tsx` — landing / login redirect
- [ ] `app/dashboard/page.tsx` — document list + upload zone
- [ ] `components/DropZone.tsx` — drag-and-drop file upload (react-dropzone)
- [ ] `components/ChatWindow.tsx` — chat UI with message history
- [ ] `components/CitationPanel.tsx` — sidebar showing source excerpts for last answer
- [ ] `components/DocumentList.tsx` — list uploaded docs with delete button + ingestion `status` badge (poll while `processing`)
- [ ] Stream assistant answers token-by-token (consume the `/query` SSE stream)
- [ ] API calls to FastAPI backend via `fetch` or `axios`
- [ ] Tailwind CSS styling — clean, minimal, dark/light mode

### You (User) do:
- [ ] Run `npm run dev` and test in browser
- [ ] Upload a document via drag-and-drop UI
- [ ] Ask a question in the chat, confirm answer + citations appear

**Reply "continue" when frontend is functional.**

---

## Phase 8 — Auth (NextAuth.js)

> Note: NextAuth does **not** own credentials — it delegates to FastAPI's `/auth/login` (built in Phase 4) and stores the returned JWT in the session. No password handling on the Next.js side.

### AI does:
- [ ] `app/api/auth/[...nextauth]/route.ts` — credentials provider (email + password)
- [ ] Calls FastAPI `/auth/login` to validate credentials, returns JWT
- [ ] Protect dashboard routes — redirect to login if no session
- [ ] `components/LoginForm.tsx` and `components/SignupForm.tsx`
- [ ] Session stored in cookies (httpOnly)

### You (User) do:
- [ ] Test login with credentials created in Phase 6
- [ ] Confirm protected routes redirect when logged out
- [ ] Confirm session persists on page refresh

**Reply "continue" when auth works end-to-end.**

---

## Phase 9 — Docker + Deployment

### AI does:
- [ ] `Dockerfile` for FastAPI backend
- [ ] `Dockerfile` for Next.js frontend
- [ ] `docker-compose.yml` — backend + frontend + PostgreSQL + Qdrant + Redis (local dev)
- [ ] `fly.toml` for Fly.io deployment config
- [ ] **Qdrant in prod:** either attach a Fly.io persistent volume (or you lose all vectors on restart) **or** point prod at the Qdrant Cloud instance from Phase 0 and skip self-hosting
- [ ] Pin dependency versions (GraphRAG + LlamaIndex + qdrant-client can clash) — use `uv`/`poetry`
- [ ] Environment variable wiring for production

### You (User) do:
- [ ] Run `docker-compose up` locally — confirm everything starts
- [ ] Create Fly.io account → `flyctl launch` → set env vars → `flyctl deploy`
- [ ] Test live URL end-to-end

**Reply "continue" when deployed.**

---

## Phase 10 — Testing & Polish

### AI does:
- [ ] Error states: empty query, unsupported file type, Qdrant down
- [ ] Loading spinners on upload and query
- [ ] File size limit (max 10MB per upload)
- [ ] `pytest` suite (ingestion, retrieval, auth) + GitHub Actions CI
- [ ] Pipeline observability/tracing (Langfuse or LangSmith) to debug retrieval quality
- [ ] README with setup instructions and live URL

### You (User) do:
- [ ] Test with 3–4 different document types
- [ ] Test multi-hop query across 2 documents
- [ ] Screenshot for portfolio / resume

---

## Commit Convention

| Prefix | Example |
|---|---|
| `feat:` | `feat: add GraphRAG multi-hop query service` |
| `fix:` | `fix: citation chunk_id mismatch on PDF pages` |
| `chore:` | `chore: docker-compose for local qdrant` |
| `style:` | `style: chat UI citation panel layout` |

---

## Priority Order

| Priority | Phases | Result |
|---|---|---|
| **Must** | 0 → 1 → 2 → 4 → 7 | Upload + basic vector search + chat UI |
| **Strong** | + 3 (GraphRAG) + 5 (citations) | Multi-hop reasoning + source grounding |
| **Complete** | + 6 (RBAC) + 8 (auth) + 9 (deploy) | Production-ready, live URL |

---

*Reply **"Phase 0 ready"** to start building.*
