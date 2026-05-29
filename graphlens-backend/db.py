"""SQLAlchemy engine, session, and declarative base.

Phase 4 creates tables via `init_db()` (run `python -m scripts.init_db`).
Phase 6 replaces that with proper Alembic migrations.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

_connect_args = {}
if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url, pool_pre_ping=True, connect_args=_connect_args
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a DB session that always closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables for all registered models (Phase 4 convenience)."""
    import models.db_models  # noqa: F401 — ensure models are registered

    Base.metadata.create_all(bind=engine)
