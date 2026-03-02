import pytest
from unittest.mock import patch, MagicMock
from app.graph.nodes.voice_synthesizer import voice_synthesizer


@pytest.mark.asyncio
async def test_synthesizes_all_segments():
    fake_audio = b"fake-audio-bytes"

    mock_client = MagicMock()
    mock_client.text_to_speech.convert.return_value = iter([fake_audio])

    with patch("app.graph.nodes.voice_synthesizer.ElevenLabs", return_value=mock_client):
        state = {
            "segments": [
                {"speaker": "narrator", "voice_type": "narrator", "text": "Once upon a time."},
                {"speaker": "Arjun", "voice_type": "child", "text": "Hello!"},
                {"speaker": "King", "voice_type": "male", "text": "Welcome!"},
            ],
        }
        result = await voice_synthesizer(state)
        assert len(result["audio_segments"]) == 3
        assert all(isinstance(a, bytes) for a in result["audio_segments"])


@pytest.mark.asyncio
async def test_maps_voice_types_to_voice_ids():
    calls = []

    mock_client = MagicMock()
    def capture_call(**kwargs):
        calls.append(kwargs)
        return iter([b"audio"])
    mock_client.text_to_speech.convert.side_effect = capture_call

    with patch("app.graph.nodes.voice_synthesizer.ElevenLabs", return_value=mock_client):
        state = {
            "segments": [
                {"speaker": "narrator", "voice_type": "narrator", "text": "Text."},
                {"speaker": "Queen", "voice_type": "female", "text": "Text."},
            ],
        }
        result = await voice_synthesizer(state)
        assert len(calls) == 2
        # Verify different voice IDs used
        assert calls[0]["voice_id"] != calls[1]["voice_id"]
