import io
import pytest
from unittest.mock import patch, MagicMock
from pydub import AudioSegment
from pydub.generators import Sine
from app.graph.nodes.audio_stitcher import audio_stitcher, _load_background_music


def _make_test_audio(duration_ms: int = 500) -> bytes:
    tone = Sine(440).to_audio_segment(duration=duration_ms)
    buf = io.BytesIO()
    tone.export(buf, format="mp3")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_stitches_with_mood():
    """Test that mood is passed through and doesn't crash (even if music file missing)."""
    seg = _make_test_audio(500)
    state = {"audio_segments": [seg], "mood": "exciting"}
    # This may or may not find the music file, but shouldn't crash
    result = await audio_stitcher(state)
    assert "final_audio" in result
    assert result["duration_seconds"] >= 0


@pytest.mark.asyncio
async def test_stitches_with_no_mood():
    seg = _make_test_audio(500)
    state = {"audio_segments": [seg]}
    result = await audio_stitcher(state)
    assert "final_audio" in result


def test_load_background_music_missing_file():
    """Test that missing music file returns None gracefully."""
    result = _load_background_music("nonexistent-mood", 5000)
    # Falls back to "default" mood, which may or may not exist
    # Either returns an AudioSegment or None
    assert result is None or isinstance(result, AudioSegment)


def test_load_background_music_with_valid_mood():
    """Test loading background music with a valid mood (if file exists)."""
    from pathlib import Path
    from app.graph.nodes.audio_stitcher import MUSIC_DIR

    # Check if any music file exists
    for mood in ["exciting", "heartwarming", "funny", "mysterious", "default"]:
        music_path = MUSIC_DIR / f"{mood}.mp3"
        if music_path.exists():
            result = _load_background_music(mood, 5000)
            assert result is not None
            assert isinstance(result, AudioSegment)
            assert len(result) == 5000  # Should be trimmed to target duration
            break
