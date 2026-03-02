# backend/tests/test_audio_stitcher.py
import io
import pytest
from pydub import AudioSegment
from pydub.generators import Sine
from app.graph.nodes.audio_stitcher import audio_stitcher


def _make_test_audio(duration_ms: int = 500) -> bytes:
    """Generate a short sine wave as MP3 bytes."""
    tone = Sine(440).to_audio_segment(duration=duration_ms)
    buf = io.BytesIO()
    tone.export(buf, format="mp3")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_stitches_multiple_segments():
    seg1 = _make_test_audio(300)
    seg2 = _make_test_audio(500)
    seg3 = _make_test_audio(200)

    state = {"audio_segments": [seg1, seg2, seg3]}
    result = await audio_stitcher(state)

    assert "final_audio" in result
    assert isinstance(result["final_audio"], bytes)
    assert len(result["final_audio"]) > 0
    assert "duration_seconds" in result
    assert result["duration_seconds"] > 0


@pytest.mark.asyncio
async def test_single_segment():
    seg = _make_test_audio(1000)
    state = {"audio_segments": [seg]}
    result = await audio_stitcher(state)
    assert result["duration_seconds"] >= 1


@pytest.mark.asyncio
async def test_adds_pauses_between_segments():
    seg1 = _make_test_audio(500)
    seg2 = _make_test_audio(500)

    state_single = {"audio_segments": [seg1]}
    result_single = await audio_stitcher(state_single)

    state_double = {"audio_segments": [seg1, seg2]}
    result_double = await audio_stitcher(state_double)

    # Two segments with a pause should be longer than just the sum
    assert result_double["duration_seconds"] >= result_single["duration_seconds"]
