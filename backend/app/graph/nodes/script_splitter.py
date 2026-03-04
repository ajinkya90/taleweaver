import logging
import re

from app.graph.state import Segment, StoryState

logger = logging.getLogger(__name__)

# Pattern matches: CharacterName: "dialogue text"
DIALOGUE_PATTERN = re.compile(r'(\w[\w\s]*?):\s*"([^"]+)"')


def _assign_voice_type(speaker: str, kid_name: str) -> str:
    if speaker == "narrator":
        return "narrator"
    if speaker.lower() == kid_name.lower():
        return "child"
    female_hints = {"queen", "princess", "mother", "mom", "sister", "aunt", "rani", "goddess", "witch", "fairy"}
    if speaker.lower() in female_hints:
        return "female"
    return "male"


async def script_splitter(state: StoryState) -> dict:
    text = state["story_text"]
    kid_name = state["kid_name"]
    segments: list[Segment] = []

    last_end = 0
    for match in DIALOGUE_PATTERN.finditer(text):
        start = match.start()
        narrator_text = text[last_end:start].strip()
        if narrator_text:
            segments.append({
                "speaker": "narrator",
                "voice_type": "narrator",
                "text": narrator_text,
            })

        speaker = match.group(1).strip()
        dialogue = match.group(2).strip()
        segments.append({
            "speaker": speaker,
            "voice_type": _assign_voice_type(speaker, kid_name),
            "text": dialogue,
        })
        last_end = match.end()

    remaining = text[last_end:].strip()
    if remaining:
        segments.append({
            "speaker": "narrator",
            "voice_type": "narrator",
            "text": remaining,
        })

    if not segments:
        segments.append({
            "speaker": "narrator",
            "voice_type": "narrator",
            "text": text.strip(),
        })

    voice_types = {}
    for seg in segments:
        vt = seg["voice_type"]
        voice_types[vt] = voice_types.get(vt, 0) + 1

    logger.info(f"Split into {len(segments)} segments: {voice_types}")

    return {"segments": segments}
