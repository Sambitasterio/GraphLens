"""Phase 4 auth tests — signup, login, JWT, and protected-route enforcement."""
from services.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


# ── primitives ─────────────────────────────────────────────────────
def test_password_hash_roundtrip():
    h = hash_password("s3cret!")
    assert h != "s3cret!"  # not stored in plaintext
    assert verify_password("s3cret!", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    token = create_access_token("user-123", "admin")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "admin"


# ── endpoints ──────────────────────────────────────────────────────
def test_signup_then_login(client):
    r = client.post("/auth/signup", json={"email": "a@b.com", "password": "pw12345"})
    assert r.status_code == 201, r.text
    assert r.json()["email"] == "a@b.com"
    assert r.json()["role"] == "user"

    # OAuth2 form login uses `username` for the email
    r = client.post("/auth/login", data={"username": "a@b.com", "password": "pw12345"})
    assert r.status_code == 200, r.text
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_duplicate_signup_rejected(client):
    client.post("/auth/signup", json={"email": "dup@b.com", "password": "pw12345"})
    r = client.post("/auth/signup", json={"email": "dup@b.com", "password": "pw12345"})
    assert r.status_code == 400


def test_login_wrong_password(client):
    client.post("/auth/signup", json={"email": "c@b.com", "password": "pw12345"})
    r = client.post("/auth/login", data={"username": "c@b.com", "password": "nope"})
    assert r.status_code == 401


def test_me_returns_current_user(client):
    client.post("/auth/signup", json={"email": "me@b.com", "password": "pw12345"})
    login = client.post("/auth/login", data={"username": "me@b.com", "password": "pw12345"})
    token = login.json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "me@b.com"


def test_documents_requires_auth(client):
    assert client.get("/documents").status_code == 401


def test_documents_list_empty_when_authed(client):
    client.post("/auth/signup", json={"email": "d@b.com", "password": "pw12345"})
    login = client.post("/auth/login", data={"username": "d@b.com", "password": "pw12345"})
    token = login.json()["access_token"]
    r = client.get("/documents", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []
