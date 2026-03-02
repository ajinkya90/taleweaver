import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.graph.pipeline import create_story_pipeline


def test_pipeline_creates_graph():
    pipeline = create_story_pipeline()
    assert pipeline is not None


@pytest.mark.asyncio
async def test_pipeline_runs_all_nodes():
    """Integration test with all nodes mocked."""
    nodes_called = []

    async def mock_story_writer(state):
        nodes_called.append("story_writer")
        return {
            "story_text": 'Narrator: "Once upon a time." Arjun: "Hello!"',
            "title": "Test Story"
        }

    async def mock_script_splitter(state):
        nodes_called.append("script_splitter")
        return {
            "segments": [
                {"speaker": "narrator", "voice_type": "narrator", "text": "Once upon a time."},
                {"speaker": "Arjun", "voice_type": "child", "text": "Hello!"},
            ]
        }

    async def mock_voice_synthesizer(state):
        nodes_called.append("voice_synthesizer")
        return {"audio_segments": [b"audio1", b"audio2"]}

    async def mock_audio_stitcher(state):
        nodes_called.append("audio_stitcher")
        return {"final_audio": b"final-audio", "duration_seconds": 120}

    with patch("app.graph.pipeline.story_writer", mock_story_writer), \
         patch("app.graph.pipeline.script_splitter", mock_script_splitter), \
         patch("app.graph.pipeline.voice_synthesizer", mock_voice_synthesizer), \
         patch("app.graph.pipeline.audio_stitcher", mock_audio_stitcher):

        pipeline = create_story_pipeline()
        result = await pipeline.ainvoke({
            "kid_name": "Arjun",
            "kid_age": 7,
            "kid_details": "",
            "story_type": "custom",
            "genre": "fantasy",
            "description": "A test story",
            "event_id": None,
            "event_data": None,
            "story_text": "",
            "title": "",
            "segments": [],
            "audio_segments": [],
            "final_audio": b"",
            "duration_seconds": 0,
            "error": None,
        })

    assert nodes_called == ["story_writer", "script_splitter", "voice_synthesizer", "audio_stitcher"]
    assert result["title"] == "Test Story"
    assert result["final_audio"] == b"final-audio"
