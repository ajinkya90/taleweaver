"""Tests for my-stories routes (/api/my-stories/*)."""

import contextlib
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

AUTH_HEADERS = {"Authorization": "Bearer dummy"}

USER_EMAIL = "user@test.com"


def _mock_user_auth():
    """Return context managers that simulate user@test.com being authenticated."""
    return [
        patch("app.main.settings.google_client_id", "fake-client-id"),
        patch("app.main._verify_google_token", return_value={"email": USER_EMAIL}),
        patch("app.main.db_get_allowed_emails", new_callable=AsyncMock, return_value={USER_EMAIL}),
    ]


def _apply(patches):
    """Apply a list of patches using ExitStack."""
    stack = contextlib.ExitStack()
    for p in patches:
        stack.enter_context(p)
    return stack


# ---------------------------------------------------------------------------
# GET /api/my-stories — 401 when auth is enabled but token is invalid
# ---------------------------------------------------------------------------


def test_list_my_stories_returns_401_without_valid_auth():
    """Enable auth by setting google_client_id, but don't mock _verify_google_token.
    The real verification will fail, producing a 401."""
    with patch("app.main.settings.google_client_id", "fake-client-id"):
        resp = client.get("/api/my-stories", headers=AUTH_HEADERS)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/my-stories — paginated list
# ---------------------------------------------------------------------------


def test_list_my_stories_returns_paginated():
    mock_stories = [
        {"id": 1, "title": "Story A", "created_at": datetime(2026, 3, 1, tzinfo=timezone.utc)},
        {"id": 2, "title": "Story B", "created_at": None},
    ]
    with _apply(_mock_user_auth()):
        with patch("app.routes.my_stories.get_user_stories", new_callable=AsyncMock, return_value=mock_stories):
            with patch("app.routes.my_stories.get_user_stories_count", new_callable=AsyncMock, return_value=5):
                resp = client.get("/api/my-stories?limit=2&offset=0", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["stories"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    # created_at should be serialized as ISO string when present
    assert data["stories"][0]["created_at"] == "2026-03-01T00:00:00+00:00"
    assert data["stories"][1]["created_at"] is None


def test_list_my_stories_clamps_negative_offset():
    with _apply(_mock_user_auth()):
        with patch("app.routes.my_stories.get_user_stories", new_callable=AsyncMock, return_value=[]):
            with patch("app.routes.my_stories.get_user_stories_count", new_callable=AsyncMock, return_value=0):
                resp = client.get("/api/my-stories?offset=-5", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["offset"] == 0


# ---------------------------------------------------------------------------
# GET /api/my-stories/{id} — story detail
# ---------------------------------------------------------------------------


def test_get_my_story_returns_detail():
    mock_story = {
        "id": 7,
        "title": "A Tale",
        "created_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
        "job_id": "xyz-123",
    }
    with _apply(_mock_user_auth()):
        with patch("app.routes.my_stories.get_user_story", new_callable=AsyncMock, return_value=mock_story):
            resp = client.get("/api/my-stories/7", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 7
    assert data["title"] == "A Tale"
    assert data["created_at"] == "2026-04-01T00:00:00+00:00"
    assert data["job_id"] == "xyz-123"


def test_get_my_story_returns_404_when_not_found():
    with _apply(_mock_user_auth()):
        with patch("app.routes.my_stories.get_user_story", new_callable=AsyncMock, return_value=None):
            resp = client.get("/api/my-stories/999", headers=AUTH_HEADERS)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/my-stories/{id}/audio — audio download
# ---------------------------------------------------------------------------


def test_get_my_story_audio_returns_bytes():
    mock_story = {"id": 3, "title": "Audio Story"}
    mock_audio = b"\xff\xfb\x90\x00" * 100  # fake MP3 bytes
    with _apply(_mock_user_auth()):
        with patch("app.routes.my_stories.get_user_story", new_callable=AsyncMock, return_value=mock_story):
            with patch("app.routes.my_stories.get_story_audio", new_callable=AsyncMock, return_value=mock_audio):
                resp = client.get("/api/my-stories/3/audio", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/mpeg"
    assert resp.content == mock_audio


def test_get_my_story_audio_returns_404_when_story_missing():
    with _apply(_mock_user_auth()):
        with patch("app.routes.my_stories.get_user_story", new_callable=AsyncMock, return_value=None):
            resp = client.get("/api/my-stories/3/audio", headers=AUTH_HEADERS)
    assert resp.status_code == 404


def test_get_my_story_audio_returns_404_when_no_audio():
    mock_story = {"id": 3, "title": "Story Without Audio"}
    with _apply(_mock_user_auth()):
        with patch("app.routes.my_stories.get_user_story", new_callable=AsyncMock, return_value=mock_story):
            with patch("app.routes.my_stories.get_story_audio", new_callable=AsyncMock, return_value=None):
                resp = client.get("/api/my-stories/3/audio", headers=AUTH_HEADERS)
    assert resp.status_code == 404
