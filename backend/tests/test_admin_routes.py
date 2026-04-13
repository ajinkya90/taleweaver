"""Tests for admin routes (/api/admin/*)."""

import contextlib
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, PropertyMock

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

AUTH_HEADERS = {"Authorization": "Bearer dummy"}

ADMIN_EMAIL = "admin@test.com"
USER_EMAIL = "user@test.com"


def _mock_admin_auth():
    """Return context managers that simulate admin@test.com being authenticated and admin."""
    return [
        patch("app.main.settings.google_client_id", "fake-client-id"),
        patch("app.main._verify_google_token", return_value={"email": ADMIN_EMAIL}),
        patch("app.main.db_get_allowed_emails", new_callable=AsyncMock, return_value={ADMIN_EMAIL}),
        patch("app.routes.admin.get_admin_emails", return_value={ADMIN_EMAIL}),
    ]


def _mock_nonadmin_auth():
    """Return context managers that simulate user@test.com being authenticated but not admin."""
    return [
        patch("app.main.settings.google_client_id", "fake-client-id"),
        patch("app.main._verify_google_token", return_value={"email": USER_EMAIL}),
        patch("app.main.db_get_allowed_emails", new_callable=AsyncMock, return_value={USER_EMAIL}),
        patch("app.routes.admin.get_admin_emails", return_value={ADMIN_EMAIL}),
    ]


def _apply(patches):
    """Apply a list of patches using ExitStack."""
    stack = contextlib.ExitStack()
    for p in patches:
        stack.enter_context(p)
    return stack


# ---------------------------------------------------------------------------
# GET /api/admin/me
# ---------------------------------------------------------------------------


def test_me_returns_admin_true_for_admin():
    with _apply(_mock_admin_auth()):
        resp = client.get("/api/admin/me", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_admin"] is True
    assert data["email"] == ADMIN_EMAIL


def test_me_returns_admin_false_for_nonadmin():
    with _apply(_mock_nonadmin_auth()):
        resp = client.get("/api/admin/me", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_admin"] is False
    assert data["email"] == USER_EMAIL


# ---------------------------------------------------------------------------
# GET /api/admin/emails
# ---------------------------------------------------------------------------


def test_list_emails_forbidden_for_nonadmin():
    with _apply(_mock_nonadmin_auth()):
        resp = client.get("/api/admin/emails", headers=AUTH_HEADERS)
    assert resp.status_code == 403


def test_list_emails_returns_list_for_admin():
    mock_emails = [
        {"email": "a@test.com", "added_at": datetime(2026, 1, 1, tzinfo=timezone.utc)},
        {"email": "b@test.com", "added_at": None},
    ]
    with _apply(_mock_admin_auth()):
        with patch("app.routes.admin.list_allowed_emails", new_callable=AsyncMock, return_value=mock_emails):
            resp = client.get("/api/admin/emails", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["emails"]) == 2
    assert data["emails"][0]["email"] == "a@test.com"
    # added_at should be serialized as ISO string
    assert data["emails"][0]["added_at"] == "2026-01-01T00:00:00+00:00"


# ---------------------------------------------------------------------------
# POST /api/admin/emails
# ---------------------------------------------------------------------------


def test_add_email_success():
    with _apply(_mock_admin_auth()):
        with patch("app.routes.admin.add_allowed_email", new_callable=AsyncMock, return_value=True):
            resp = client.post("/api/admin/emails", json={"email": "new@example.com"}, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "added"
    assert resp.json()["email"] == "new@example.com"


def test_add_email_duplicate_returns_409():
    with _apply(_mock_admin_auth()):
        with patch("app.routes.admin.add_allowed_email", new_callable=AsyncMock, return_value=False):
            resp = client.post("/api/admin/emails", json={"email": "dup@example.com"}, headers=AUTH_HEADERS)
    assert resp.status_code == 409


def test_add_email_invalid_returns_400():
    with _apply(_mock_admin_auth()):
        resp = client.post("/api/admin/emails", json={"email": "not-an-email"}, headers=AUTH_HEADERS)
    assert resp.status_code == 400


def test_add_email_forbidden_for_nonadmin():
    with _apply(_mock_nonadmin_auth()):
        resp = client.post("/api/admin/emails", json={"email": "x@example.com"}, headers=AUTH_HEADERS)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/admin/emails/{email}
# ---------------------------------------------------------------------------


def test_remove_email_success():
    with _apply(_mock_admin_auth()):
        with patch("app.routes.admin.remove_allowed_email", new_callable=AsyncMock, return_value=True):
            resp = client.delete("/api/admin/emails/other@example.com", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "removed"


def test_remove_own_email_returns_400():
    with _apply(_mock_admin_auth()):
        resp = client.delete(f"/api/admin/emails/{ADMIN_EMAIL}", headers=AUTH_HEADERS)
    assert resp.status_code == 400
    assert "own email" in resp.json()["detail"].lower()


def test_remove_nonexistent_email_returns_404():
    with _apply(_mock_admin_auth()):
        with patch("app.routes.admin.remove_allowed_email", new_callable=AsyncMock, return_value=False):
            resp = client.delete("/api/admin/emails/gone@example.com", headers=AUTH_HEADERS)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/admin/stories
# ---------------------------------------------------------------------------


def test_stories_list_forbidden_for_nonadmin():
    with _apply(_mock_nonadmin_auth()):
        resp = client.get("/api/admin/stories", headers=AUTH_HEADERS)
    assert resp.status_code == 403


def test_stories_list_returns_paginated_for_admin():
    mock_stories = [
        {"id": 1, "title": "Story A", "created_at": datetime(2026, 3, 1, tzinfo=timezone.utc), "job_id": None},
        {"id": 2, "title": "Story B", "created_at": None, "job_id": "abc-123"},
    ]
    with _apply(_mock_admin_auth()):
        with patch("app.routes.admin.get_stories", new_callable=AsyncMock, return_value=mock_stories):
            with patch("app.routes.admin.get_stories_count", new_callable=AsyncMock, return_value=42):
                resp = client.get("/api/admin/stories?limit=2&offset=0", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 42
    assert len(data["stories"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0


def test_stories_list_clamps_negative_offset():
    with _apply(_mock_admin_auth()):
        with patch("app.routes.admin.get_stories", new_callable=AsyncMock, return_value=[]):
            with patch("app.routes.admin.get_stories_count", new_callable=AsyncMock, return_value=0):
                resp = client.get("/api/admin/stories?offset=-5", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["offset"] == 0


# ---------------------------------------------------------------------------
# GET /api/admin/stories/{story_id}
# ---------------------------------------------------------------------------


def test_story_detail_returns_story_for_admin():
    mock_story = {"id": 7, "title": "A Tale", "created_at": datetime(2026, 4, 1, tzinfo=timezone.utc), "job_id": "xyz"}
    with _apply(_mock_admin_auth()):
        with patch("app.routes.admin.get_story", new_callable=AsyncMock, return_value=mock_story):
            resp = client.get("/api/admin/stories/7", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 7
    assert data["job_id"] == "xyz"
    assert data["created_at"] == "2026-04-01T00:00:00+00:00"


def test_story_detail_returns_404_for_missing():
    with _apply(_mock_admin_auth()):
        with patch("app.routes.admin.get_story", new_callable=AsyncMock, return_value=None):
            resp = client.get("/api/admin/stories/999", headers=AUTH_HEADERS)
    assert resp.status_code == 404
