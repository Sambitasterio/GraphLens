"""SQLAlchemy ORM models.

Phase 4 needs `users` (auth, pulled forward from Phase 6) and `documents`
(upload/list/delete + async ingestion status). Phase 6 adds
`document_access` and `query_logs` on top.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
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
