"""GraphLens FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import settings
from routers import auth, documents, query
from services.ratelimit import limiter

app = FastAPI(
    title="GraphLens API",
    description="Enterprise Document Intelligence Platform",
    version="0.1.0",
)

# Rate limiting (slowapi)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(query.router)
