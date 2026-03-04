import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_custom_story_returns_job():
    with patch("app.routes.story.run_pipeline", new_callable=AsyncMock):
        response = client.post("/api/story/custom", json={
            "kid": {"name": "Arjun", "age": 7},
            "genre": "fantasy",
            "description": "A magical adventure"
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"
        assert data["current_stage"] == "writing"


def test_create_historical_story_returns_job():
    with patch("app.routes.story.run_pipeline", new_callable=AsyncMock):
        response = client.post("/api/story/historical", json={
            "kid": {"name": "Arjun", "age": 7},
            "event_id": "shivaji-agra-escape"
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data


def test_historical_story_invalid_event():
    response = client.post("/api/story/historical", json={
        "kid": {"name": "Arjun", "age": 7},
        "event_id": "nonexistent-event"
    })
    assert response.status_code == 404


def test_get_job_status_not_found():
    response = client.get("/api/story/status/nonexistent-id")
    assert response.status_code == 404


def test_get_audio_not_found():
    response = client.get("/api/story/audio/nonexistent-id")
    assert response.status_code == 404


def test_get_audio_returns_correct_headers():
    from app.routes.story import jobs
    job_id = "test-audio-headers"
    jobs[job_id] = {
        "status": "complete",
        "final_audio": b"\xff\xfb\x90\x00" * 100,  # fake MP3 bytes
    }
    response = client.get(f"/api/story/audio/{job_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.headers["content-length"] == str(400)
    assert response.headers["accept-ranges"] == "bytes"
    assert "inline" in response.headers["content-disposition"]
    # Cleanup
    del jobs[job_id]


def test_get_audio_download_mode():
    from app.routes.story import jobs
    job_id = "test-audio-download"
    jobs[job_id] = {
        "status": "complete",
        "final_audio": b"\xff\xfb\x90\x00" * 100,
    }
    response = client.get(f"/api/story/audio/{job_id}?download=true")
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    del jobs[job_id]
