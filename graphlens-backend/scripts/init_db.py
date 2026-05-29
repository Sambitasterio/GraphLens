"""Create database tables (Phase 4 convenience; Alembic replaces this in Phase 6).

Usage (from graphlens-backend/, venv active, Postgres running):
    python -m scripts.init_db
"""
from db import init_db

if __name__ == "__main__":
    init_db()
    print("Tables created.")
