"""Role-based access control for documents.

A user can access a document if they own it OR it's been shared with them.
Admins can access everything. The query path uses `accessible_doc_ids` to
scope Qdrant retrieval; document privacy is enforced here, centrally.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from models.db_models import Document, DocumentAccess, User


def accessible_doc_ids(db: Session, user: User) -> list[str] | None:
    """Doc ids the user may retrieve.

    Returns None for admins (meaning *unrestricted* — no filter), otherwise a
    list of owned + shared doc ids (possibly empty).
    """
    if user.role == "admin":
        return None

    owned = db.query(Document.id).filter(Document.owner_id == user.id)
    shared = db.query(DocumentAccess.doc_id).filter(DocumentAccess.user_id == user.id)
    return list({row[0] for row in owned.all()} | {row[0] for row in shared.all()})


def can_access(db: Session, user: User, doc: Document) -> bool:
    if user.role == "admin" or doc.owner_id == user.id:
        return True
    grant = (
        db.query(DocumentAccess)
        .filter(DocumentAccess.doc_id == doc.id, DocumentAccess.user_id == user.id)
        .first()
    )
    return grant is not None


def grant_access(db: Session, doc_id: str, user_id: str) -> DocumentAccess:
    """Share a document with a user (idempotent)."""
    existing = (
        db.query(DocumentAccess)
        .filter(DocumentAccess.doc_id == doc_id, DocumentAccess.user_id == user_id)
        .first()
    )
    if existing:
        return existing
    grant = DocumentAccess(doc_id=doc_id, user_id=user_id)
    db.add(grant)
    db.commit()
    db.refresh(grant)
    return grant
