import time
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.routes.story import jobs, _format_kid_details, _cleanup_old_jobs, _friendly_error, JOB_TTL_SECONDS

client = TestClient(app)


class FakeKid:
    favorite_animal = "tiger"
    favorite_color = "blue"
    hobby = "drawing"
    best_friend = "Riya"
    pet_name = "Bruno"
    personality = "adventurous"


class MinimalKid:
    favorite_animal = None
    favorite_color = None
    hobby = None
    best_friend = None
    pet_name = None
    personality = None


def test_format_kid_details_all_fields():
    details = _format_kid_details(FakeKid())
    assert "tiger" in details
    assert "blue" in details
    assert "drawing" in details
    assert "Riya" in details
    assert "Bruno" in details
    assert "adventurous" in details


def test_format_kid_details_no_fields():
    details = _format_kid_details(MinimalKid())
    assert details == ""


def test_format_kid_details_partial():
    kid = MinimalKid()
    kid.favorite_animal = "dog"
    kid.hobby = "reading"
    details = _format_kid_details(kid)
    assert "dog" in details
    assert "reading" in details
    assert "color" not in details


def test_cleanup_old_jobs():
    # Add an expired job
    old_id = "expired-job"
    jobs[old_id] = {
        "status": "complete",
        "created_at": time.time() - JOB_TTL_SECONDS - 100,
    }
    # Add a fresh job
    fresh_id = "fresh-job"
    jobs[fresh_id] = {
        "status": "complete",
        "created_at": time.time(),
    }
    _cleanup_old_jobs()
    assert old_id not in jobs
    assert fresh_id in jobs
    # Cleanup
    del jobs[fresh_id]


def test_cleanup_skips_processing_jobs():
    job_id = "processing-job"
    jobs[job_id] = {
        "status": "processing",
        "created_at": time.time() - JOB_TTL_SECONDS - 100,
    }
    _cleanup_old_jobs()
    assert job_id in jobs
    del jobs[job_id]


def test_get_job_status_complete():
    job_id = "test-complete-status"
    jobs[job_id] = {
        "status": "complete",
        "title": "Test Story",
        "duration_seconds": 120,
        "final_audio": b"fake",
        "transcript": "Once upon a time...",
        "created_at": time.time(),
    }
    response = client.get(f"/api/story/status/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "complete"
    assert data["title"] == "Test Story"
    assert data["duration_seconds"] == 120
    assert data["audio_url"] == f"/api/story/audio/{job_id}"
    assert data["transcript"] == "Once upon a time..."
    del jobs[job_id]


def test_get_job_status_complete_without_transcript():
    """Jobs completed before transcript feature should return empty string."""
    job_id = "test-complete-no-transcript"
    jobs[job_id] = {
        "status": "complete",
        "title": "Old Story",
        "duration_seconds": 60,
        "final_audio": b"fake",
        "created_at": time.time(),
    }
    response = client.get(f"/api/story/status/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == ""
    del jobs[job_id]


def test_get_job_status_processing():
    job_id = "test-processing-status"
    jobs[job_id] = {
        "status": "processing",
        "current_stage": "synthesizing",
        "created_at": time.time(),
    }
    response = client.get(f"/api/story/status/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["current_stage"] == "synthesizing"
    del jobs[job_id]


def test_get_job_status_failed():
    job_id = "test-failed-status"
    jobs[job_id] = {
        "status": "failed",
        "error": "Something broke",
        "created_at": time.time(),
    }
    response = client.get(f"/api/story/status/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    del jobs[job_id]


def test_get_audio_not_ready():
    job_id = "test-audio-not-ready"
    jobs[job_id] = {
        "status": "processing",
        "created_at": time.time(),
    }
    response = client.get(f"/api/story/audio/{job_id}")
    assert response.status_code == 404
    assert "not ready" in response.json()["detail"].lower()
    del jobs[job_id]


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_custom_story_with_mood_and_length():
    with patch("app.routes.story.run_pipeline", new_callable=AsyncMock):
        response = client.post("/api/story/custom", json={
            "kid": {"name": "Arjun", "age": 7},
            "genre": "fantasy",
            "description": "A magical adventure",
            "mood": "exciting",
            "length": "short",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"


def test_create_custom_story_invalid_mood():
    response = client.post("/api/story/custom", json={
        "kid": {"name": "Arjun", "age": 7},
        "genre": "fantasy",
        "description": "A magical adventure",
        "mood": "scary",
    })
    assert response.status_code == 422


def test_create_custom_story_invalid_length():
    response = client.post("/api/story/custom", json={
        "kid": {"name": "Arjun", "age": 7},
        "genre": "fantasy",
        "description": "A magical adventure",
        "length": "extra-long",
    })
    assert response.status_code == 422


def test_create_custom_story_name_too_long():
    response = client.post("/api/story/custom", json={
        "kid": {"name": "A" * 51, "age": 7},
        "genre": "fantasy",
        "description": "A magical adventure",
    })
    assert response.status_code == 422


def test_create_custom_story_description_too_long():
    response = client.post("/api/story/custom", json={
        "kid": {"name": "Arjun", "age": 7},
        "genre": "fantasy",
        "description": "A" * 501,
    })
    assert response.status_code == 422


def test_create_historical_story_with_mood_and_length():
    with patch("app.routes.story.run_pipeline", new_callable=AsyncMock):
        response = client.post("/api/story/historical", json={
            "kid": {"name": "Arjun", "age": 7},
            "event_id": "shivaji-agra-escape",
            "mood": "exciting",
            "length": "medium",
        })
        assert response.status_code == 200


def test_friendly_error_quota():
    e = Exception("status_code: 401, body: {'detail': {'status': 'quota_exceeded'}}")
    assert "quota" in _friendly_error(e).lower()


def test_friendly_error_invalid_key():
    e = Exception("invalid_api_key: The API key is not valid")
    assert "API key" in _friendly_error(e)


def test_friendly_error_rate_limit():
    e = Exception("rate_limit_exceeded: Too many requests")
    assert "rate limit" in _friendly_error(e).lower()


def test_friendly_error_timeout():
    e = Exception("Request timed out after 30 seconds")
    assert "timed out" in _friendly_error(e).lower()


def test_friendly_error_llm_provider():
    e = Exception("anthropic.APIError: invalid x-api-key")
    assert "LLM provider" in _friendly_error(e)


def test_friendly_error_unknown():
    e = Exception("some random crash")
    assert "unexpected" in _friendly_error(e).lower()


def test_get_job_status_failed_returns_error():
    job_id = "test-failed-with-error"
    jobs[job_id] = {
        "status": "failed",
        "error": "ElevenLabs voice generation quota exceeded.",
        "created_at": time.time(),
    }
    response = client.get(f"/api/story/status/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert "quota" in data["error"].lower()
    del jobs[job_id]


def test_load_event_caching():
    """Verify that _load_events returns cached data on second call."""
    from app.routes.story import _load_events
    events1 = _load_events()
    events2 = _load_events()
    assert events1 is events2  # Same object, not reloaded
