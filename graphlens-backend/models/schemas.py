"""Pydantic request/response schemas for the API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── auth ───────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── documents ──────────────────────────────────────────────────────
class DocumentOut(BaseModel):
    id: str
    filename: str
    status: str
    chunk_count: int
    uploaded_at: datetime
    error: str | None = None

    model_config = {"from_attributes": True}


# ── query ──────────────────────────────────────────────────────────
class Citation(BaseModel):
    chunk_id: str
    filename: str | None = None
    page: int | None = None
    text: str


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    use_graph: bool = True
    graph_method: str = Field(default="local", pattern="^(local|global)$")


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]


class QueryLogOut(BaseModel):
    id: str
    query: str
    answer: str
    citations: list[Citation] = []
    used_graph: bool = False
    total_tokens: int = 0
    cost_usd: float = 0.0
    created_at: datetime

    model_config = {"from_attributes": True}
