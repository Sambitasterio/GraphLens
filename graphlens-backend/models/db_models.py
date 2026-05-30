"""SQLAlchemy ORM models.

Phase 4 needs `users` (auth, pulled forward from Phase 6) and `documents`
(upload/list/delete + async ingestion status). Phase 6 adds
`document_access` and `query_logs` on top.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from db import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")  # "user" | "admin"
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship(
        "Document", back_populates="owner", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uuid)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    # async ingestion lifecycle
    status = Column(String, nullable=False, default="processing")  # processing|ready|failed
    chunk_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="documents")


class DocumentAccess(Base):
    """Many-to-many grant: a document shared with a (non-owner) user."""

    __tablename__ = "document_access"
    __table_args__ = (UniqueConstraint("doc_id", "user_id", name="uq_doc_user"),)

    id = Column(String, primary_key=True, default=_uuid)
    doc_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    granted_at = Column(DateTime, default=datetime.utcnow)


class QueryLog(Base):
    """Audit trail of every query: the question, the cited answer, and the
    token/cost footprint. Cheap to record now, painful to backfill later."""

    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    citations = Column(JSON, default=list)  # list of citation dicts
    used_graph = Column(Boolean, default=False)
    graph_method = Column(String, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
