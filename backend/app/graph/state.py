from typing import Optional
from typing_extensions import TypedDict


class Segment(TypedDict):
    speaker: str
    voice_type: str  # "narrator", "male", "female", "child"
    text: str


class StoryState(TypedDict):
    # Input
    kid_name: str
    kid_age: int
    kid_details: str  # Formatted optional details
    story_type: str  # "custom" or "historical"
    genre: Optional[str]
    description: Optional[str]
    event_id: Optional[str]
    event_data: Optional[dict]
    mood: Optional[str]
    length: Optional[str]

    # Pipeline outputs
    story_text: str
    title: str
    segments: list[Segment]
    audio_segments: list[bytes]
    final_audio: bytes
    duration_seconds: int
    error: Optional[str]
