import gc
import io
import logging
from pathlib import Path
from typing import Optional

from pydub import AudioSegment

from app.graph.state import StoryState

logger = logging.getLogger(__name__)

PAUSE_MS = 500  # Half-second pause between segments
MUSIC_DIR = Path(__file__).parent.parent.parent / "data" / "music"
MUSIC_VOLUME_DB = -18


def _load_background_music(mood: Optional[str], target_duration_ms: int) -> Optional[AudioSegment]:
    """Load and loop background music to match story duration, memory-efficient."""
    mood_key = mood if mood in ("exciting", "heartwarming", "funny", "mysterious") else "default"
    music_path = MUSIC_DIR / f"{mood_key}.mp3"

    if not music_path.exists():
        logger.warning(f"Background music not found: {music_path}")
        return None

    music = AudioSegment.from_mp3(str(music_path))
    # Convert to mono and reduce sample rate to save memory
    music = music.set_channels(1).set_frame_rate(22050)

    # Build looped music incrementally instead of multiplying all at once
    result = AudioSegment.empty()
    while len(result) < target_duration_ms:
        result += music

    result = result[:target_duration_ms]
    result = result.fade_in(2000).fade_out(3000)
    logger.info(f"Background music: mood={mood_key}, duration={target_duration_ms}ms")
    return result + MUSIC_VOLUME_DB


async def audio_stitcher(state: StoryState) -> dict:
    pause = AudioSegment.silent(duration=PAUSE_MS)
    combined = AudioSegment.empty()

    for i, audio_bytes in enumerate(state["audio_segments"]):
        segment = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
        combined += segment
        if i < len(state["audio_segments"]) - 1:
            combined += pause

    logger.info(f"Stitched {len(state['audio_segments'])} segments, narration duration={len(combined)}ms")

    # Convert narration to mono to reduce memory for overlay
    combined = combined.set_channels(1)

    mood = state.get("mood")
    bg_music = _load_background_music(mood, len(combined))
    if bg_music is not None:
        # Match sample rate for overlay
        bg_music = bg_music.set_frame_rate(combined.frame_rate)
        combined = combined.overlay(bg_music)
        del bg_music
        gc.collect()

    buf = io.BytesIO()
    combined.export(buf, format="mp3", bitrate="64k")
    final_bytes = buf.getvalue()
    duration_seconds = int(len(combined) / 1000)
    del combined
    gc.collect()

    logger.info(f"Final audio: duration={duration_seconds}s, size={len(final_bytes)} bytes")

    return {"final_audio": final_bytes, "duration_seconds": duration_seconds}
