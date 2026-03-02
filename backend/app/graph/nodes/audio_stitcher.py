# backend/app/graph/nodes/audio_stitcher.py
import io

from pydub import AudioSegment

from app.graph.state import StoryState

PAUSE_MS = 500  # Half-second pause between segments


async def audio_stitcher(state: StoryState) -> dict:
    pause = AudioSegment.silent(duration=PAUSE_MS)
    combined = AudioSegment.empty()

    for i, audio_bytes in enumerate(state["audio_segments"]):
        segment = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
        combined += segment
        if i < len(state["audio_segments"]) - 1:
            combined += pause

    buf = io.BytesIO()
    combined.export(buf, format="mp3")
    final_bytes = buf.getvalue()
    duration_seconds = int(len(combined) / 1000)

    return {"final_audio": final_bytes, "duration_seconds": duration_seconds}
