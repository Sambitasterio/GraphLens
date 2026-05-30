"""Promote a user to admin (for RBAC validation).

Usage (from graphlens-backend/, venv active):
    python -m scripts.make_admin someone@example.com
"""
import sys

from db import SessionLocal
from models.db_models import User


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.make_admin <email>")
        return 2
    email = sys.argv[1]
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"No user with email {email}")
            return 1
        user.role = "admin"
        db.commit()
        print(f"{email} is now an admin.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
