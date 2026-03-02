# backend/app/graph/nodes/audio_stitcher.py
import io
from pathlib import Path
from typing import Optional

from pydub import AudioSegment

from app.graph.state import StoryState

PAUSE_MS = 500  # Half-second pause between segments
MUSIC_DIR = Path(__file__).parent.parent / "data" / "music"
MUSIC_VOLUME_DB = -18


def _load_background_music(mood: Optional[str], target_duration_ms: int) -> Optional[AudioSegment]:
    """Load and loop background music to match story duration."""
    mood_key = mood if mood in ("exciting", "heartwarming", "funny", "mysterious") else "default"
    music_path = MUSIC_DIR / f"{mood_key}.mp3"

    if not music_path.exists():
        return None

    music = AudioSegment.from_mp3(str(music_path))
    # Loop music to cover the full story duration
    loops_needed = (target_duration_ms // len(music)) + 1
    looped = music * loops_needed
    # Trim to exact duration with fade out
    trimmed = looped[:target_duration_ms]
    trimmed = trimmed.fade_in(2000).fade_out(3000)
    return trimmed + MUSIC_VOLUME_DB


async def audio_stitcher(state: StoryState) -> dict:
    pause = AudioSegment.silent(duration=PAUSE_MS)
    combined = AudioSegment.empty()

    for i, audio_bytes in enumerate(state["audio_segments"]):
        segment = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
        combined += segment
        if i < len(state["audio_segments"]) - 1:
            combined += pause

    # Mix background music if available
    mood = state.get("mood")
    bg_music = _load_background_music(mood, len(combined))
    if bg_music is not None:
        combined = combined.overlay(bg_music)

    buf = io.BytesIO()
    combined.export(buf, format="mp3")
    final_bytes = buf.getvalue()
    duration_seconds = int(len(combined) / 1000)

    return {"final_audio": final_bytes, "duration_seconds": duration_seconds}
