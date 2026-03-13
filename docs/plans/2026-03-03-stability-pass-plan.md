# Stability Pass Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix audio cutoff, broken seek bar, poor story quality (switch to Sonnet), and add logging/transcript storage.

**Architecture:** Surgical fixes to existing files. No new pipeline nodes or component libraries. Add Python `logging` module throughout backend pipeline nodes. Fix audio endpoint headers for proper streaming. Fix frontend player state management.

**Tech Stack:** Python logging, FastAPI Response headers, React audio event handlers, Claude Sonnet 4.5

---

### Task 1: Fix Audio Endpoint Headers

**Files:**
- Modify: `backend/app/routes/story.py:172-185`
- Test: `backend/tests/test_story_routes.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_story_routes.py`:

```python
def test_get_audio_returns_correct_headers():
    from app.routes.story import jobs
    job_id = "test-audio-headers"
    jobs[job_id] = {
        "status": "complete",
        "final_audio": b"\xff\xfb\x90\x00" * 100,  # fake MP3 bytes
    }
    response = client.get(f"/api/story/audio/{job_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.headers["content-length"] == str(400)
    assert response.headers["accept-ranges"] == "bytes"
    assert "inline" in response.headers["content-disposition"]
    # Cleanup
    del jobs[job_id]


def test_get_audio_download_mode():
    from app.routes.story import jobs
    job_id = "test-audio-download"
    jobs[job_id] = {
        "status": "complete",
        "final_audio": b"\xff\xfb\x90\x00" * 100,
    }
    response = client.get(f"/api/story/audio/{job_id}?download=true")
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    del jobs[job_id]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_story_routes.py::test_get_audio_returns_correct_headers tests/test_story_routes.py::test_get_audio_download_mode -v`
Expected: FAIL (missing content-length, accept-ranges headers; disposition says "attachment" not "inline")

**Step 3: Write minimal implementation**

Replace the `get_audio` endpoint in `backend/app/routes/story.py:172-185`:

```python
@router.get("/audio/{job_id}")
async def get_audio(job_id: str, download: bool = False):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    if job["status"] != "complete" or "final_audio" not in job:
        raise HTTPException(status_code=404, detail="Audio not ready")

    audio_bytes = job["final_audio"]
    disposition = "attachment" if download else "inline"

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'{disposition}; filename="story-{job_id}.mp3"',
            "Content-Length": str(len(audio_bytes)),
            "Accept-Ranges": "bytes",
        },
    )
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_story_routes.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/routes/story.py backend/tests/test_story_routes.py
git commit -m "fix: add Content-Length and Accept-Ranges headers to audio endpoint

Switches Content-Disposition from attachment to inline for streaming
playback. Adds ?download=true query param for download button."
```

---

### Task 2: Switch LLM to Sonnet with max_tokens

**Files:**
- Modify: `backend/app/graph/llm.py:6-19`
- Test: `backend/tests/test_llm.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_llm.py`:

```python
def test_get_llm_anthropic_uses_sonnet():
    with patch("app.graph.llm.settings") as mock_settings:
        mock_settings.llm_provider = "anthropic"
        mock_settings.anthropic_api_key = "test-key"
        llm = get_llm()
        assert llm is not None
        assert "sonnet" in llm.model


def test_get_llm_has_max_tokens():
    with patch("app.graph.llm.settings") as mock_settings:
        mock_settings.llm_provider = "anthropic"
        mock_settings.anthropic_api_key = "test-key"
        llm = get_llm()
        assert llm.max_tokens == 8192
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_llm.py::test_get_llm_anthropic_uses_sonnet tests/test_llm.py::test_get_llm_has_max_tokens -v`
Expected: FAIL (model is "claude-haiku-4-5-20251001", no max_tokens attribute)

**Step 3: Write minimal implementation**

Replace `backend/app/graph/llm.py` entirely:

```python
from langchain_core.language_models import BaseChatModel

from app.config import settings


def get_llm() -> BaseChatModel:
    provider = settings.llm_provider.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(api_key=settings.groq_api_key, model="llama-3.3-70b-versatile", max_tokens=8192)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=settings.openai_api_key, model="gpt-4o", max_tokens=8192)
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(api_key=settings.anthropic_api_key, model="claude-sonnet-4-5-20250514", max_tokens=8192)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_llm.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/graph/llm.py backend/tests/test_llm.py
git commit -m "feat: switch default LLM to Claude Sonnet 4.5 with max_tokens=8192

Improves story quality significantly over Haiku. Sets explicit
max_tokens on all providers to prevent silent truncation."
```

---

### Task 3: Fix Historical Story mood/length Passthrough

**Files:**
- Modify: `backend/app/routes/story.py:117-135`
- Modify: `backend/app/models/requests.py:24-27`
- Test: `backend/tests/test_story_routes.py`
- Test: `backend/tests/test_models.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_models.py`:

```python
def test_historical_story_request_accepts_mood_and_length():
    from app.models.requests import HistoricalStoryRequest
    req = HistoricalStoryRequest(
        kid={"name": "Arjun", "age": 7},
        event_id="shivaji-agra-escape",
        mood="exciting",
        length="medium",
    )
    assert req.mood == "exciting"
    assert req.length == "medium"


def test_historical_story_request_mood_length_optional():
    from app.models.requests import HistoricalStoryRequest
    req = HistoricalStoryRequest(
        kid={"name": "Arjun", "age": 7},
        event_id="shivaji-agra-escape",
    )
    assert req.mood is None
    assert req.length is None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_models.py::test_historical_story_request_accepts_mood_and_length tests/test_models.py::test_historical_story_request_mood_length_optional -v`
Expected: FAIL (HistoricalStoryRequest has no mood/length fields)

**Step 3: Write minimal implementation**

In `backend/app/models/requests.py`, update `HistoricalStoryRequest`:

```python
class HistoricalStoryRequest(BaseModel):
    kid: KidProfile
    event_id: str
    mood: Optional[str] = None      # exciting, heartwarming, funny, mysterious
    length: Optional[str] = None    # short, medium, long
```

In `backend/app/routes/story.py`, update historical state (lines 126-127):

```python
        "mood": request.mood,
        "length": request.length,
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_models.py tests/test_story_routes.py -v`
Expected: ALL PASS

**Step 5: Update frontend API client**

In `frontend/src/api/client.ts`, update `createHistoricalStory` to pass mood/length:

```typescript
export async function createHistoricalStory(
  kid: KidProfile,
  eventId: string,
  mood?: string,
  length?: string,
): Promise<JobCreatedResponse> {
  const res = await fetch(`${BASE}/story/historical`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kid, event_id: eventId, mood, length }),
  });
  return res.json();
}
```

**Step 6: Commit**

```bash
git add backend/app/models/requests.py backend/app/routes/story.py backend/tests/test_models.py frontend/src/api/client.ts
git commit -m "fix: pass mood and length through for historical stories

Historical stories were hardcoded to mood=None and length=None,
ignoring user selections. Now passes through from request."
```

---

### Task 4: Add Logging to Pipeline Nodes + Transcript Storage

**Files:**
- Modify: `backend/app/graph/nodes/story_writer.py`
- Modify: `backend/app/graph/nodes/script_splitter.py`
- Modify: `backend/app/graph/nodes/voice_synthesizer.py`
- Modify: `backend/app/graph/nodes/audio_stitcher.py`
- Modify: `.gitignore`

**Step 1: Add `logs/` to `.gitignore`**

Append to `.gitignore`:

```
backend/logs/
```

**Step 2: Add logging and transcript saving to story_writer.py**

Replace `backend/app/graph/nodes/story_writer.py` entirely:

```python
import logging
import os
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.llm import get_llm
from app.graph.state import StoryState
from app.prompts.custom_story import build_custom_story_prompt
from app.prompts.historical_story import build_historical_story_prompt

logger = logging.getLogger(__name__)

LOGS_DIR = Path(__file__).parent.parent.parent / "logs" / "stories"


def _save_transcript(state: StoryState, title: str, story_text: str):
    """Save story transcript to file for evaluation."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{state['kid_name'].lower().replace(' ', '_')}.txt"
        filepath = LOGS_DIR / filename

        word_count = len(story_text.split())
        content = f"""=== STORY TRANSCRIPT ===
Title: {title}
Generated: {datetime.now().isoformat()}
Kid: {state['kid_name']}, age {state['kid_age']}
Story Type: {state['story_type']}
Genre: {state.get('genre', 'N/A')}
Mood: {state.get('mood', 'N/A')}
Length: {state.get('length', 'N/A')}
Word Count: {word_count}
========================

{story_text}
"""
        filepath.write_text(content)
        logger.info(f"Transcript saved to {filepath}")
    except Exception as e:
        logger.warning(f"Failed to save transcript: {e}")


async def story_writer(state: StoryState) -> dict:
    llm = get_llm()

    if state["story_type"] == "custom":
        prompt = build_custom_story_prompt(
            name=state["kid_name"],
            age=state["kid_age"],
            details=state["kid_details"],
            genre=state["genre"],
            description=state["description"],
            mood=state.get("mood"),
            length=state.get("length"),
        )
    else:
        prompt = build_historical_story_prompt(
            name=state["kid_name"],
            age=state["kid_age"],
            details=state["kid_details"],
            event_data=state["event_data"],
            mood=state.get("mood"),
            length=state.get("length"),
        )

    logger.info(f"Generating {state['story_type']} story for {state['kid_name']} (age {state['kid_age']}), mood={state.get('mood')}, length={state.get('length')}")

    response = await llm.ainvoke([
        SystemMessage(content="You are a children's storyteller. Follow the instructions exactly."),
        HumanMessage(content=prompt),
    ])

    text = response.content
    title = ""
    story_text = text

    if "TITLE:" in text and "STORY:" in text:
        parts = text.split("STORY:", 1)
        title_part = parts[0]
        story_text = parts[1].strip()
        title = title_part.replace("TITLE:", "").strip()
    else:
        logger.warning("LLM response missing TITLE:/STORY: markers, using raw text")

    word_count = len(story_text.split())
    logger.info(f"Story generated: title='{title}', word_count={word_count}")
    logger.info(f"--- FULL TRANSCRIPT ---\n{story_text}\n--- END TRANSCRIPT ---")

    _save_transcript(state, title, story_text)

    return {"story_text": story_text, "title": title}
```

**Step 3: Add logging to script_splitter.py**

Add logging at the top and after processing in `backend/app/graph/nodes/script_splitter.py`:

```python
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
```

**Step 4: Add logging to voice_synthesizer.py**

```python
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


async def voice_synthesizer(state: StoryState) -> dict:
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    audio_segments: list[bytes] = []

    total_start = time.time()
    for i, segment in enumerate(state["segments"]):
        voice_id = _get_voice_id(segment["voice_type"])
        seg_start = time.time()
        audio_iter = client.text_to_speech.convert(
            voice_id=voice_id,
            text=segment["text"],
            model_id="eleven_multilingual_v2",
        )
        audio_bytes = b"".join(audio_iter)
        audio_segments.append(audio_bytes)
        elapsed = time.time() - seg_start
        logger.info(f"TTS segment {i+1}/{len(state['segments'])}: voice={segment['voice_type']}, chars={len(segment['text'])}, bytes={len(audio_bytes)}, time={elapsed:.1f}s")

    total_elapsed = time.time() - total_start
    logger.info(f"TTS complete: {len(audio_segments)} segments in {total_elapsed:.1f}s")

    return {"audio_segments": audio_segments}
```

**Step 5: Add logging to audio_stitcher.py**

```python
import io
import logging
from pathlib import Path
from typing import Optional

from pydub import AudioSegment

from app.graph.state import StoryState

logger = logging.getLogger(__name__)

PAUSE_MS = 500  # Half-second pause between segments
MUSIC_DIR = Path(__file__).parent.parent / "data" / "music"
MUSIC_VOLUME_DB = -18


def _load_background_music(mood: Optional[str], target_duration_ms: int) -> Optional[AudioSegment]:
    """Load and loop background music to match story duration."""
    mood_key = mood if mood in ("exciting", "heartwarming", "funny", "mysterious") else "default"
    music_path = MUSIC_DIR / f"{mood_key}.mp3"

    if not music_path.exists():
        logger.warning(f"Background music not found: {music_path}")
        return None

    music = AudioSegment.from_mp3(str(music_path))
    # Loop music to cover the full story duration
    loops_needed = (target_duration_ms // len(music)) + 1
    looped = music * loops_needed
    # Trim to exact duration with fade out
    trimmed = looped[:target_duration_ms]
    trimmed = trimmed.fade_in(2000).fade_out(3000)
    logger.info(f"Background music: mood={mood_key}, loops={loops_needed}, duration={target_duration_ms}ms")
    return trimmed + MUSIC_VOLUME_DB


async def audio_stitcher(state: StoryState) -> dict:
    pause = AudioSegment.silent(duration=PAUSE_MS)
    combined = AudioSegment.empty()

    for i, audio_bytes in enumerate(state["audio_segments"]):
        segment = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
        combined += segment
        if i < len(state["audio_segments"]) - 1:
            combined += pause

    logger.info(f"Stitched {len(state['audio_segments'])} segments, narration duration={len(combined)}ms")

    # Mix background music if available
    mood = state.get("mood")
    bg_music = _load_background_music(mood, len(combined))
    if bg_music is not None:
        combined = combined.overlay(bg_music)

    buf = io.BytesIO()
    combined.export(buf, format="mp3")
    final_bytes = buf.getvalue()
    duration_seconds = int(len(combined) / 1000)

    logger.info(f"Final audio: duration={duration_seconds}s, size={len(final_bytes)} bytes")

    return {"final_audio": final_bytes, "duration_seconds": duration_seconds}
```

**Step 6: Configure logging in main.py**

Add at the top of `backend/app/main.py`, before other imports:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
```

**Step 7: Run all backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: ALL PASS (logging is additive, doesn't change behavior)

**Step 8: Commit**

```bash
git add backend/app/graph/nodes/story_writer.py backend/app/graph/nodes/script_splitter.py backend/app/graph/nodes/voice_synthesizer.py backend/app/graph/nodes/audio_stitcher.py backend/app/main.py .gitignore
git commit -m "feat: add logging and transcript storage to pipeline nodes

Logs story transcript, word count, segment breakdown, TTS timing,
and final audio stats. Saves full transcripts to backend/logs/stories/
for quality evaluation."
```

---

### Task 5: Fix Audio Player (Seek Bar, Play State, Error Handling)

**Files:**
- Modify: `frontend/src/components/StoryScreen.tsx`
- Modify: `frontend/src/api/client.ts`

**Step 1: Rewrite StoryScreen.tsx audio player logic**

Replace `frontend/src/components/StoryScreen.tsx` entirely:

```tsx
import { useRef, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Props {
  isGenerating: boolean;
  currentStage: string;
  title: string;
  audioUrl: string;
  durationSeconds: number;
  onCreateAnother: () => void;
}

const STAGE_LABELS: Record<string, string> = {
  writing: "Weaving your tale...",
  splitting: "Giving voice to characters...",
  synthesizing: "Recording the narration...",
  stitching: "Binding the magic...",
};

const STAGES = Object.keys(STAGE_LABELS);

const formatTime = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
};

export default function StoryScreen({
  isGenerating,
  currentStage,
  title,
  audioUrl,
  durationSeconds,
  onCreateAnother,
}: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(durationSeconds);
  const [isSeeking, setIsSeeking] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);

  // Sync duration from audio element metadata (more accurate than backend estimate)
  useEffect(() => {
    setDuration(durationSeconds);
  }, [durationSeconds]);

  const handleLoadedMetadata = () => {
    if (audioRef.current && audioRef.current.duration && isFinite(audioRef.current.duration)) {
      setDuration(audioRef.current.duration);
    }
  };

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch((err) => {
        console.error("Playback failed:", err);
        setIsPlaying(false);
      });
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const t = Number(e.target.value);
    if (audioRef.current) audioRef.current.currentTime = t;
    setCurrentTime(t);
  };

  const handleSeekStart = () => setIsSeeking(true);
  const handleSeekEnd = () => setIsSeeking(false);

  const handleTimeUpdate = () => {
    if (!isSeeking && audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleAudioError = () => {
    setAudioError("Failed to load audio. Please try again.");
    setIsPlaying(false);
  };

  // Build download URL with ?download=true
  const downloadUrl = audioUrl ? `${audioUrl}?download=true` : "";

  const currentStageIndex = STAGES.indexOf(currentStage);
  const label = STAGE_LABELS[currentStage] || "Creating your story...";

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      <AnimatePresence mode="wait">
        {isGenerating ? (
          /* ─── Phase 1: Generation Animation ─── */
          <motion.div
            key="generating"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col items-center space-y-8"
          >
            {/* Pulsing Orb */}
            <motion.div
              className="w-32 h-32 rounded-full"
              style={{
                background:
                  "radial-gradient(circle, #a78bfa 0%, #7c3aed 50%, #4c1d95 100%)",
                boxShadow:
                  "0 0 40px rgba(124, 58, 237, 0.6), 0 0 80px rgba(124, 58, 237, 0.3), 0 0 120px rgba(124, 58, 237, 0.1)",
              }}
              animate={{
                scale: [1, 1.15, 1],
                opacity: [0.8, 1, 0.8],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />

            {/* Stage Label */}
            <AnimatePresence mode="wait">
              <motion.p
                key={currentStage}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                className="text-xl font-display text-glow text-ethereal"
              >
                {label}
              </motion.p>
            </AnimatePresence>

            {/* Progress Dots */}
            <div className="flex gap-3">
              {STAGES.map((stage, i) => {
                const isCompleted = i < currentStageIndex;
                const isCurrent = i === currentStageIndex;
                return (
                  <motion.div
                    key={stage}
                    className="w-3 h-3 rounded-full"
                    style={{
                      backgroundColor: isCompleted
                        ? "#7c3aed"
                        : isCurrent
                          ? "#a78bfa"
                          : "rgba(255, 255, 255, 0.15)",
                    }}
                    animate={
                      isCurrent
                        ? { scale: [1, 1.4, 1], opacity: [0.7, 1, 0.7] }
                        : {}
                    }
                    transition={
                      isCurrent
                        ? { duration: 1, repeat: Infinity, ease: "easeInOut" }
                        : {}
                    }
                  />
                );
              })}
            </div>

            {/* Subtitle */}
            <p className="text-sm text-starlight/40">
              This usually takes about a minute
            </p>
          </motion.div>
        ) : (
          audioUrl && (
            /* ─── Phase 2: Audio Player ─── */
            <motion.div
              key="player"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="flex flex-col items-center space-y-8 w-full max-w-md"
            >
              {/* Story Title */}
              <h2 className="text-3xl md:text-4xl font-display text-glow text-center leading-snug">
                {title}
              </h2>

              {/* Player Card */}
              <div className="glass-card w-full p-6 space-y-6">
                {audioError ? (
                  <p className="text-red-400 text-center text-sm">{audioError}</p>
                ) : (
                  <>
                    {/* Seek Bar */}
                    <input
                      type="range"
                      min={0}
                      max={duration || 1}
                      step={0.1}
                      value={currentTime}
                      onChange={handleSeek}
                      onMouseDown={handleSeekStart}
                      onMouseUp={handleSeekEnd}
                      onTouchStart={handleSeekStart}
                      onTouchEnd={handleSeekEnd}
                      className="w-full h-2 rounded-full appearance-none cursor-pointer
                        bg-white/10
                        [&::-webkit-slider-thumb]:appearance-none
                        [&::-webkit-slider-thumb]:w-4
                        [&::-webkit-slider-thumb]:h-4
                        [&::-webkit-slider-thumb]:rounded-full
                        [&::-webkit-slider-thumb]:bg-mystic
                        [&::-webkit-slider-thumb]:shadow-[0_0_10px_rgba(124,58,237,0.6)]
                        [&::-webkit-slider-runnable-track]:rounded-full
                        [&::-moz-range-thumb]:w-4
                        [&::-moz-range-thumb]:h-4
                        [&::-moz-range-thumb]:rounded-full
                        [&::-moz-range-thumb]:bg-mystic
                        [&::-moz-range-thumb]:border-none
                        [&::-moz-range-thumb]:shadow-[0_0_10px_rgba(124,58,237,0.6)]
                        accent-mystic"
                    />

                    {/* Time Display */}
                    <div className="flex justify-between text-sm text-starlight/40">
                      <span>{formatTime(currentTime)}</span>
                      <span>{formatTime(duration)}</span>
                    </div>

                    {/* Play/Pause Button */}
                    <div className="flex justify-center">
                      <motion.button
                        onClick={togglePlay}
                        whileTap={{ scale: 0.9 }}
                        whileHover={{
                          boxShadow:
                            "0 0 30px rgba(124, 58, 237, 0.6), 0 0 60px rgba(124, 58, 237, 0.3)",
                        }}
                        className="w-20 h-20 rounded-full flex items-center justify-center text-3xl text-white cursor-pointer"
                        style={{
                          background:
                            "linear-gradient(135deg, #7c3aed, #6d28d9)",
                          boxShadow:
                            "0 0 20px rgba(124, 58, 237, 0.4), 0 0 40px rgba(124, 58, 237, 0.15)",
                        }}
                      >
                        {isPlaying ? "⏸" : "▶"}
                      </motion.button>
                    </div>
                  </>
                )}

                {/* Hidden Audio Element */}
                <audio
                  ref={audioRef}
                  src={audioUrl}
                  preload="auto"
                  onLoadedMetadata={handleLoadedMetadata}
                  onTimeUpdate={handleTimeUpdate}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onEnded={() => setIsPlaying(false)}
                  onError={handleAudioError}
                />
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 w-full">
                <a
                  href={downloadUrl}
                  download
                  className="glass-card px-6 py-3 text-center font-semibold text-starlight transition-all hover:text-glow"
                >
                  Download MP3
                </a>
                <button
                  onClick={onCreateAnother}
                  className="btn-glow flex-1 text-center"
                >
                  Create Another Story
                </button>
              </div>
            </motion.div>
          )
        )}
      </AnimatePresence>
    </div>
  );
}
```

Key changes:
- `onLoadedMetadata` gets actual duration from audio element
- `onPlay`/`onPause` listeners sync React state with actual audio state
- `togglePlay` handles `play()` promise rejection
- `isSeeking` flag prevents slider jitter during drag
- `onError` handler shows error message
- `preload="auto"` ensures full audio is buffered
- `step={0.1}` for smoother seeking
- `max={duration || 1}` prevents broken slider when duration is 0
- Download link uses `?download=true` for proper attachment headers

**Step 2: Run frontend type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/StoryScreen.tsx
git commit -m "fix: audio player seeking, play state sync, and error handling

Fixes: slider jitter during drag (isSeeking flag), play state desync
(onPlay/onPause listeners), missing duration (onLoadedMetadata),
play() promise rejection, no error UI on failed audio load.
Uses preload=auto for full buffering."
```

---

### Task 6: Add Logging Configuration to run_pipeline

**Files:**
- Modify: `backend/app/routes/story.py:48-62`

**Step 1: Add stage-tracking logging to run_pipeline**

In `backend/app/routes/story.py`, update `run_pipeline` to log stage transitions and errors:

```python
import logging

logger = logging.getLogger(__name__)

async def run_pipeline(job_id: str, state: dict):
    try:
        pipeline = create_story_pipeline()

        logger.info(f"[{job_id}] Starting pipeline: type={state['story_type']}, kid={state['kid_name']}, age={state['kid_age']}")
        jobs[job_id]["current_stage"] = "writing"
        result = await pipeline.ainvoke(state)

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["current_stage"] = "done"
        jobs[job_id]["title"] = result["title"]
        jobs[job_id]["duration_seconds"] = result["duration_seconds"]
        jobs[job_id]["final_audio"] = result["final_audio"]

        logger.info(f"[{job_id}] Pipeline complete: title='{result['title']}', duration={result['duration_seconds']}s")
    except Exception as e:
        logger.error(f"[{job_id}] Pipeline failed: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
```

Also add `import logging` at the top and `logger = logging.getLogger(__name__)` after imports.

**Step 2: Run all backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add backend/app/routes/story.py
git commit -m "feat: add logging to story route pipeline runner

Logs pipeline start, completion, and failures with job IDs for
tracing story generation issues."
```

---

### Task 7: Final Verification

**Step 1: Run all backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: ALL PASS

**Step 2: Run frontend type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Start backend and verify logging output**

Run: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000`
Expected: Server starts with logging configured, shows `[asctime] [module] INFO:` format

**Step 4: Start frontend and verify player loads**

Run: `cd frontend && npm run dev`
Expected: Dev server starts, UI loads at http://localhost:5173
