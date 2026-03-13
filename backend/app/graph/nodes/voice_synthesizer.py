import asyncio
import logging
import time

from elevenlabs import ElevenLabs

from app.config import settings
from app.graph.state import StoryState

logger = logging.getLogger(__name__)


def _get_voice_id(voice_type: str) -> str:
    mapping = {
        "narrator": settings.narrator_voice_id,
        "male": settings.character_male_voice_id,
        "female": settings.character_female_voice_id,
        "child": settings.character_child_voice_id,
    }
    return mapping.get(voice_type, settings.narrator_voice_id)


def _synthesize_segment(client: ElevenLabs, voice_id: str, text: str) -> bytes:
    audio_iter = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
    )
    return b"".join(audio_iter)


async def voice_synthesizer(state: StoryState) -> dict:
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    audio_segments: list[bytes] = []

    total_start = time.time()
    for i, segment in enumerate(state["segments"]):
        voice_id = _get_voice_id(segment["voice_type"])
        seg_start = time.time()
        audio_bytes = await asyncio.to_thread(
            _synthesize_segment, client, voice_id, segment["text"]
        )
        audio_segments.append(audio_bytes)
        elapsed = time.time() - seg_start
        logger.info(f"TTS segment {i+1}/{len(state['segments'])}: voice={segment['voice_type']}, chars={len(segment['text'])}, bytes={len(audio_bytes)}, time={elapsed:.1f}s")

    total_elapsed = time.time() - total_start
    logger.info(f"TTS complete: {len(audio_segments)} segments in {total_elapsed:.1f}s")

    return {"audio_segments": audio_segments}
