from elevenlabs import ElevenLabs

from app.config import settings
from app.graph.state import StoryState


def _get_voice_id(voice_type: str) -> str:
    mapping = {
        "narrator": settings.narrator_voice_id,
        "male": settings.character_male_voice_id,
        "female": settings.character_female_voice_id,
        "child": settings.character_child_voice_id,
    }
    return mapping.get(voice_type, settings.narrator_voice_id)


async def voice_synthesizer(state: StoryState) -> dict:
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    audio_segments: list[bytes] = []

    for segment in state["segments"]:
        voice_id = _get_voice_id(segment["voice_type"])
        audio_iter = client.text_to_speech.convert(
            voice_id=voice_id,
            text=segment["text"],
            model_id="eleven_multilingual_v2",
        )
        audio_bytes = b"".join(audio_iter)
        audio_segments.append(audio_bytes)

    return {"audio_segments": audio_segments}
