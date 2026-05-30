"""Document endpoints: upload (async ingestion), list, delete."""
from __future__ import annotations

import logging
import os
import tempfile

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from db import SessionLocal, get_db
from models.db_models import Document, User
from models.schemas import DocumentOut, ShareRequest
from services import access, vectorstore
from services.errors import IngestionError
from services.ingestion import ingest_document, validate_upload
from services.ratelimit import limiter
from services.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


def _process_document(doc_id: str, file_path: str, user_id: str, filename: str) -> None:
    """Background task: ingest + embed + upsert, then mark the doc ready/failed.

    Uses its own DB session since it runs after the request returns.
    """
    db = SessionLocal()
    try:
        chunks = ingest_document(
            file_path, doc_id=doc_id, user_id=user_id, filename=filename, embed=True
        )
        vectorstore.upsert_chunks(chunks)
        doc = db.get(Document, doc_id)
        if doc:
            doc.status = "ready"
            doc.chunk_count = len(chunks)
            db.commit()
        logger.info("Ingested %s (%d chunks)", filename, len(chunks))
    except Exception as exc:  # noqa: BLE001 — record failure on the row
        logger.exception("Ingestion failed for %s", filename)
        doc = db.get(Document, doc_id)
        if doc:
            doc.status = "failed"
            doc.error = str(exc)
            db.commit()
    finally:
        db.close()
        try:
            os.remove(file_path)
        except OSError:
            pass


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("20/minute")
async def upload(
    request: Request,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = await file.read()
    try:
        validate_upload(file.filename, len(data))
    except IngestionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    # Persist to a temp file the background task will read then delete.
    suffix = os.path.splitext(file.filename)[1]
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)

    doc = Document(owner_id=user.id, filename=file.filename, status="processing")
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background.add_task(_process_document, doc.id, path, user.id, file.filename)
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """List documents the caller can access (owned + shared; admins see all)."""
    ids = access.accessible_doc_ids(db, user)
    q = db.query(Document)
    if ids is not None:  # non-admin
        if not ids:
            return []
        q = q.filter(Document.id.in_(ids))
    docs = q.order_by(Document.uploaded_at.desc()).all()
    return [
        DocumentOut(
            id=d.id, filename=d.filename, status=d.status,
            chunk_count=d.chunk_count or 0, uploaded_at=d.uploaded_at,
            error=d.error, owned=(d.owner_id == user.id),
        )
        for d in docs
    ]


@router.post("/{doc_id}/share", status_code=status.HTTP_201_CREATED)
def share_document(
    doc_id: str,
    payload: ShareRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Grant another user access to a document. Owner or admin only."""
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if doc.owner_id != user.id and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed to share this document")

    target = db.query(User).filter(User.email == payload.user_email).first()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Target user not found")
    if target.id == doc.owner_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Owner already has access")

    access.grant_access(db, doc_id, target.id)
    return {"doc_id": doc_id, "shared_with": target.email}


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.get(Document, doc_id)
    # Only the owner or an admin may delete.
    if doc is None or (doc.owner_id != user.id and user.role != "admin"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    vectorstore.delete_by_doc(doc_id)
    db.delete(doc)
    db.commit()
