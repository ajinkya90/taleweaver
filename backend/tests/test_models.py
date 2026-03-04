import pytest
from app.models.requests import KidProfile, CustomStoryRequest, HistoricalStoryRequest
from app.models.responses import JobCreatedResponse, JobStatusResponse, JobCompleteResponse


def test_kid_profile_required_fields():
    kid = KidProfile(name="Arjun", age=7)
    assert kid.name == "Arjun"
    assert kid.age == 7
    assert kid.favorite_animal is None


def test_kid_profile_all_fields():
    kid = KidProfile(
        name="Arjun", age=7, favorite_animal="tiger",
        favorite_color="blue", hobby="drawing",
        best_friend="Riya", pet_name="Bruno",
        personality="adventurous"
    )
    assert kid.favorite_animal == "tiger"
    assert kid.personality == "adventurous"


def test_kid_profile_age_validation():
    with pytest.raises(Exception):
        KidProfile(name="Arjun", age=2)
    with pytest.raises(Exception):
        KidProfile(name="Arjun", age=13)


def test_custom_story_request():
    req = CustomStoryRequest(
        kid=KidProfile(name="Arjun", age=7),
        genre="fantasy",
        description="A magical paintbrush"
    )
    assert req.genre == "fantasy"


def test_historical_story_request():
    req = HistoricalStoryRequest(
        kid=KidProfile(name="Arjun", age=7),
        event_id="shivaji-agra-escape"
    )
    assert req.event_id == "shivaji-agra-escape"


def test_job_created_response():
    resp = JobCreatedResponse(
        job_id="abc-123",
        status="processing",
        stages=["writing", "splitting", "synthesizing", "stitching"],
        current_stage="writing"
    )
    assert resp.job_id == "abc-123"


def test_job_status_response():
    resp = JobStatusResponse(
        job_id="abc-123",
        status="processing",
        current_stage="synthesizing",
        progress=3,
        total_segments=8
    )
    assert resp.progress == 3


def test_custom_story_request_with_mood_and_length():
    req = CustomStoryRequest(
        kid=KidProfile(name="Ava", age=7),
        genre="adventure",
        description="A quest for a golden feather",
        mood="exciting",
        length="medium",
    )
    assert req.mood == "exciting"
    assert req.length == "medium"


def test_custom_story_request_mood_defaults_to_none():
    req = CustomStoryRequest(
        kid=KidProfile(name="Ava", age=7),
        genre="adventure",
        description="A quest",
    )
    assert req.mood is None
    assert req.length is None


def test_historical_story_request_accepts_mood_and_length():
    from app.models.requests import HistoricalStoryRequest
    req = HistoricalStoryRequest(
        kid={"name": "Arjun", "age": 7},
        event_id="shivaji-agra-escape",
        mood="exciting",
        length="medium",
    )
    assert req.mood == "exciting"
    assert req.length == "medium"


def test_historical_story_request_mood_length_optional():
    from app.models.requests import HistoricalStoryRequest
    req = HistoricalStoryRequest(
        kid={"name": "Arjun", "age": 7},
        event_id="shivaji-agra-escape",
    )
    assert req.mood is None
    assert req.length is None


def test_job_complete_response():
    resp = JobCompleteResponse(
        job_id="abc-123",
        status="complete",
        title="Arjun and the Magical Paintbrush",
        duration_seconds=285,
        audio_url="/api/story/audio/abc-123"
    )
    assert resp.title == "Arjun and the Magical Paintbrush"
