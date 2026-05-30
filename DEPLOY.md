# GraphLens — Deployment

## Local (Docker Compose)

Brings up Qdrant + Postgres + Redis + backend + frontend. The backend runs
`alembic upgrade head` on startup.

```bash
# optional: set a real session secret for the frontend
export AUTH_SECRET=$(openssl rand -hex 32)

docker compose up --build
```

- Frontend → http://localhost:3000
- Backend  → http://localhost:8000/docs
- Put your `OPENAI_API_KEY` in `graphlens-backend/.env` before building.

> URL wiring: the browser hits the backend at `http://localhost:8000`
> (`NEXT_PUBLIC_API_URL`, baked at build), while the frontend container reaches
> it at `http://backend:8000` (`API_INTERNAL_URL`, runtime) for NextAuth.

Stop with `docker compose down` (add `-v` to wipe data volumes).

---

## Production (Fly.io)

Two Fly apps (backend + frontend) plus managed Postgres and Qdrant Cloud.

### 1. Managed datastores
- **Postgres:** `fly postgres create` (or Supabase) → note the connection string.
- **Qdrant:** Qdrant Cloud free tier → note URL + API key. (Self-hosting Qdrant
  on Fly needs a persistent volume, or you lose all vectors on restart.)

### 2. Backend
```bash
cd graphlens-backend
fly launch --no-deploy            # uses fly.toml; pick an app name/region
fly secrets set \
  OPENAI_API_KEY=sk-... \
  DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:5432/DB \
  QDRANT_URL=https://YOUR.qdrant.cloud QDRANT_API_KEY=... \
  JWT_SECRET=$(openssl rand -hex 32) \
  CORS_ORIGINS='["https://graphlens-frontend.fly.dev"]'
fly deploy                        # entrypoint runs alembic upgrade head
```

### 3. Frontend
Set `NEXT_PUBLIC_API_URL` (build arg in fly.toml) to the backend's URL, then:
```bash
cd graphlens-frontend
fly launch --no-deploy
fly secrets set \
  AUTH_SECRET=$(openssl rand -hex 32) \
  AUTH_TRUST_HOST=true \
  API_INTERNAL_URL=https://graphlens-backend.fly.dev
fly deploy
```

### Notes
- `CORS_ORIGINS` must be a JSON array (pydantic-settings parses list env vars as JSON).
- GraphRAG indexing is a separate offline step; the deployed API degrades to
  vector-only until a graph is built and its `graphrag_workspace/output/`
  artifacts are present.
