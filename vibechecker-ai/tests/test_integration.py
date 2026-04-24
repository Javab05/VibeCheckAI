"""End-to-end integration tests for the VibeCheckAI backend.

Covers the full happy-path the Expo frontend will exercise:
    register  →  login  →  upload check-in  →  get history  →  seasonal summary

Status: SKELETON. These are expected to fail today. They will go green after:
    - Zem fixes the 6 backend route bugs (see docs/api-contract.md § "Known Bugs")
    - Zem wires `CORS(app)` into flaskApp.py (flask-cors is now in requirements.txt)
    - Henry retrains the model on 6 classes (disgust dropped)

Run:
    cd vibechecker-ai
    pip install pytest
    # from the project root so `database.*` and `backend.*` imports resolve
    python -m pytest tests/test_integration.py -v

Fresh DB per test run: the `client` fixture points SQLAlchemy at a temp sqlite
file so production `vibechecker.db` is untouched.
"""

from __future__ import annotations

import io
import os
import tempfile

import pytest


# ────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def tmp_db_path():
    """Give each test session its own sqlite file.

    We set VIBECHECKER_DB_PATH so models.py can pick it up if/when Zem wires
    it in. Until then, this fixture just documents the intent — the test will
    still hit whatever DB models.py points at by default.
    """
    fd, path = tempfile.mkstemp(suffix=".db", prefix="vibechecker-test-")
    os.close(fd)
    os.environ["VIBECHECKER_DB_PATH"] = path
    yield path
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture(scope="session")
def client(tmp_db_path):
    """Flask test client backed by a fresh DB.

    Imports happen inside the fixture so the env var is set before
    database.models binds its engine.
    """
    from database.models import Base, engine
    from backend.flaskApp import app

    Base.metadata.create_all(engine)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def registered_user(client):
    """Register a fresh user and return (user_id, email, password)."""
    email = "integration-test@example.com"
    password = "hunter2-correct-horse"
    resp = client.post(
        "/auth/register",
        json={"username": "integration", "email": email, "password": password},
    )
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert "user_id" in body
    return body["user_id"], email, password


# ────────────────────────────────────────────────────────────────────
# Auth
# ────────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_creates_user(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "username": "new_user",
                "email": "new_user@example.com",
                "password": "pw-pw-pw",
            },
        )
        assert resp.status_code == 200
        body = resp.get_json()
        # Bug #1: auth.py line 28 assigns `user_id = create_user(...)` but
        # create_user() returns a User object, not an int.
        # Once fixed, this assertion should pass.
        assert isinstance(body["user_id"], int)

    def test_register_missing_fields_returns_400(self, client):
        resp = client.post("/auth/register", json={"email": "x@y.z"})
        assert resp.status_code == 400

    def test_login_success(self, client, registered_user):
        _, email, password = registered_user
        resp = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        # Bug #2: auth.py line 64 reads `user.id`, but the column is user_id.
        assert "user_id" in body

    def test_login_wrong_password(self, client, registered_user):
        _, email, _ = registered_user
        resp = client.post(
            "/auth/login",
            json={"email": email, "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post(
            "/auth/login",
            json={"email": "nobody@nowhere.test", "password": "x"},
        )
        assert resp.status_code == 404


# ────────────────────────────────────────────────────────────────────
# Check-in upload
# ────────────────────────────────────────────────────────────────────

class TestCheckin:
    def _fake_image(self) -> tuple[io.BytesIO, str]:
        # Minimal 1x1 JPEG header bytes — not a real image, just enough
        # that request.files["image"] is non-empty. Replace with a real
        # fixture once Zem hooks up file.save().
        return io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 64), "selfie.jpg"

    def test_upload_returns_prediction(self, client, registered_user):
        user_id, _, _ = registered_user
        img, filename = self._fake_image()

        resp = client.post(
            "/checkin/upload",
            data={"user_id": str(user_id), "image": (img, filename)},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        body = resp.get_json()

        # Fields from docs/api-contract.md § "POST /checkin/upload"
        assert "checkin_id" in body
        assert "predicted_emotion" in body
        assert "confidence" in body
        assert "scores" in body
        assert 0.0 <= body["confidence"] <= 1.0

        # Bug #3: checkin.py line 13 calls create_checkin(user_id) with
        # one arg, but create_checkin() needs 5 (user_id, image_path,
        # captured_at, season, season_year). Bug #4: same file line 19 calls
        # store_emotion_result(checkin_id, emotion) with 2 args, needs 4.
        # Bug #5: file is read from request but never saved to disk.

    def test_upload_missing_user_id(self, client):
        img, filename = self._fake_image()
        resp = client.post(
            "/checkin/upload",
            data={"image": (img, filename)},
            content_type="multipart/form-data",
        )
        assert resp.status_code in (400, 422)


# ────────────────────────────────────────────────────────────────────
# History + seasonal summary
# ────────────────────────────────────────────────────────────────────

class TestHistory:
    def test_empty_history(self, client, registered_user):
        user_id, _, _ = registered_user
        # Bug #6: history.py line 7 calls get_user_history(user_id) with one
        # arg, but the helper needs (user_id, season, season_year).
        # When fixed, endpoint will need ?season= & ?season_year= query params
        # (see api-contract.md).
        resp = client.get(f"/history/{user_id}?season=winter&season_year=2026")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_history_after_upload(self, client, registered_user):
        user_id, _, _ = registered_user
        img = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 64)

        client.post(
            "/checkin/upload",
            data={"user_id": str(user_id), "image": (img, "selfie.jpg")},
            content_type="multipart/form-data",
        )

        resp = client.get(f"/history/{user_id}?season=winter&season_year=2026")
        assert resp.status_code == 200
        entries = resp.get_json()
        assert len(entries) >= 1

        row = entries[0]
        # Shape comes from Checkin.to_dict() + nested latest_result.to_dict()
        assert "checkin_id" in row
        assert "captured_at" in row
        assert "season" in row
        assert "latest_result" in row


# ────────────────────────────────────────────────────────────────────
# CORS
# ────────────────────────────────────────────────────────────────────

class TestCORS:
    """Once Zem adds `from flask_cors import CORS; CORS(app)` these pass."""

    def test_cors_header_present(self, client):
        resp = client.get(
            "/ping",
            headers={"Origin": "http://localhost:19006"},  # Expo dev server
        )
        assert resp.status_code == 200
        assert "Access-Control-Allow-Origin" in resp.headers

    def test_cors_preflight(self, client):
        resp = client.options(
            "/auth/login",
            headers={
                "Origin": "http://localhost:19006",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert resp.status_code in (200, 204)
        assert "Access-Control-Allow-Origin" in resp.headers


# ────────────────────────────────────────────────────────────────────
# Smoke
# ────────────────────────────────────────────────────────────────────

def test_root_ok(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_ping_ok(client):
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
