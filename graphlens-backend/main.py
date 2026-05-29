"""GraphLens FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

app = FastAPI(
    title="GraphLens API",
    description="Enterprise Document Intelligence Platform",
    version="0.1.0",
)

# CORS — allow the Next.js frontend during local dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health() -> dict:
    """Liveness probe used by Docker / Fly.io and Phase 0 validation."""
    return {"status": "ok", "service": "graphlens-backend", "version": "0.1.0"}


# Routers are registered as each phase lands them.
# from routers import documents, query, auth
# app.include_router(documents.router)
# app.include_router(query.router)
# app.include_router(auth.router)
