import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.routes.story import run_pipeline, jobs


@pytest.mark.asyncio
async def test_run_pipeline_success():
    """Test that run_pipeline updates job state on success."""
    job_id = "test-pipeline-success"
    jobs[job_id] = {"status": "processing", "current_stage": "writing"}

    fake_events = [
        {"story_writer": {"story_text": "A story", "title": "Test Title"}},
        {"script_splitter": {"segments": []}},
        {"voice_synthesizer": {"audio_segments": []}},
        {"audio_stitcher": {"final_audio": b"audio", "duration_seconds": 30}},
    ]

    async def fake_astream(state):
        for event in fake_events:
            yield event

    mock_pipeline = MagicMock()
    mock_pipeline.astream = fake_astream

    with patch("app.routes.story.create_story_pipeline", return_value=mock_pipeline):
        state = {
            "story_type": "custom",
            "kid_name": "Arjun",
            "kid_age": 7,
        }
        await run_pipeline(job_id, state)

    assert jobs[job_id]["status"] == "complete"
    assert jobs[job_id]["title"] == "Test Title"
    assert jobs[job_id]["duration_seconds"] == 30
    assert jobs[job_id]["final_audio"] == b"audio"
    assert jobs[job_id]["current_stage"] == "done"
    del jobs[job_id]


@pytest.mark.asyncio
async def test_run_pipeline_failure():
    """Test that run_pipeline updates job state on failure."""
    job_id = "test-pipeline-failure"
    jobs[job_id] = {"status": "processing", "current_stage": "writing"}

    with patch("app.routes.story.create_story_pipeline", side_effect=Exception("LLM error")):
        state = {"story_type": "custom", "kid_name": "Arjun", "kid_age": 7}
        await run_pipeline(job_id, state)

    assert jobs[job_id]["status"] == "failed"
    assert "LLM error" in jobs[job_id]["error"]
    del jobs[job_id]
