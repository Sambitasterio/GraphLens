"""Create database tables via create_all.

DEPRECATED for Postgres as of Phase 6 — use Alembic instead:
    alembic upgrade head
Kept only as a quick escape hatch / for ad-hoc SQLite use. Alembic
(alembic/versions/) is now the source of truth for the schema.
"""
from db import init_db

if __name__ == "__main__":
    init_db()
    print("Tables created.")
