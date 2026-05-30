"""Phase 6 RBAC tests — access scoping + sharing, on in-memory SQLite."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.db_models import Document, User
from services import access


@pytest.fixture
def db():
    from db import Base
    import models.db_models  # noqa: F401

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _seed(db):
    alice = User(id="alice", email="a@x.com", hashed_password="x", role="user")
    bob = User(id="bob", email="b@x.com", hashed_password="x", role="user")
    admin = User(id="root", email="root@x.com", hashed_password="x", role="admin")
    doc = Document(id="docA", owner_id="alice", filename="a.pdf", status="ready")
    db.add_all([alice, bob, admin, doc])
    db.commit()
    return alice, bob, admin, doc


def test_owner_sees_own_doc(db):
    alice, bob, admin, doc = _seed(db)
    assert access.accessible_doc_ids(db, alice) == ["docA"]


def test_other_user_isolated(db):
    alice, bob, admin, doc = _seed(db)
    assert access.accessible_doc_ids(db, bob) == []
    assert access.can_access(db, bob, doc) is False


def test_admin_unrestricted(db):
    alice, bob, admin, doc = _seed(db)
    assert access.accessible_doc_ids(db, admin) is None  # None == all
    assert access.can_access(db, admin, doc) is True


def test_sharing_grants_access(db):
    alice, bob, admin, doc = _seed(db)
    access.grant_access(db, "docA", "bob")
    assert access.accessible_doc_ids(db, bob) == ["docA"]
    assert access.can_access(db, bob, doc) is True


def test_grant_is_idempotent(db):
    alice, bob, admin, doc = _seed(db)
    access.grant_access(db, "docA", "bob")
    access.grant_access(db, "docA", "bob")  # no duplicate / no error
    assert access.accessible_doc_ids(db, bob) == ["docA"]
