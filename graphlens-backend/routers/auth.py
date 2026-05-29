"""Auth endpoints (signup/login, JWT issuance). Implemented in Phase 4.

FastAPI is the single source of truth for credentials; NextAuth (Phase 8)
only delegates to these endpoints.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

# POST /auth/signup
# POST /auth/login -> returns JWT
