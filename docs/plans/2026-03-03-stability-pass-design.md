# Taleweaver Stability Pass — Design

**Date**: 2026-03-03
**Goal**: Fix audio cutoff, broken seek bar, poor story quality, and add logging/transcript storage.

## Problems

1. **Audio cuts off at end** — Missing `Content-Length` header; `Content-Disposition: attachment` fights `<audio>` element streaming.
2. **Seek bar broken** — Play state desyncs from actual audio; slider jitters during drag; no `onLoadedMetadata` for duration; no error handling.
3. **Story quality is bad** — Claude Haiku produces generic/short/incoherent stories. No `max_tokens` set. Historical stories ignore mood/length.
4. **No logging** — No transcript logging anywhere. Impossible to evaluate story quality post-generation.

## Approach

Surgical bug fixes in existing architecture. No new pipeline nodes or player library rewrites.

## Changes

### 1. Audio Endpoint (`backend/app/routes/story.py`)

- Add `Content-Length` header with actual byte count
- Change `Content-Disposition` from `attachment` to `inline` for streaming playback
- Add `Accept-Ranges: bytes` header to support seeking
- Add `?download=true` query parameter to trigger download behavior when user clicks download button

### 2. Audio Player (`frontend/src/components/StoryScreen.tsx`)

- Add `onLoadedMetadata` handler — get actual duration from audio element, don't rely solely on backend prop
- Handle `audio.play()` promise rejection (browser autoplay policies)
- Add `onPlay`/`onPause` event listeners to keep React state in sync with actual audio state
- Track `isSeeking` state — while user drags slider, ignore `onTimeUpdate` to prevent jitter
- Add `onError` handler for failed audio loads with user-visible error message

### 3. LLM & Story Quality (`backend/app/graph/llm.py`, `backend/app/routes/story.py`)

- Switch default Anthropic model from `claude-haiku-4-5-20251001` to `claude-sonnet-4-5-20250514`
- Set `max_tokens=8192` explicitly on all LLM providers
- Fix historical story route: pass `request.mood` and `request.length` instead of hardcoded `None`

### 4. Logging & Transcripts

Add Python `logging` to all pipeline nodes:
- `story_writer.py` — Log full transcript, word count, title
- `script_splitter.py` — Log segment count, voice type assignments
- `voice_synthesizer.py` — Log per-segment TTS durations
- `audio_stitcher.py` — Log final audio duration, background music mood

Save transcripts to files:
- Directory: `backend/logs/stories/`
- File: `{job_id}.txt` containing title, word count, full transcript, metadata (kid name, age, genre/event, mood, length)
- Add `logs/` to `.gitignore`

### 5. Minor Fixes

- Log warning if generated word count is outside expected range for requested age+length combo
- Improve error messages in job status response when pipeline fails

## Files Changed

| File | Change |
|------|--------|
| `backend/app/routes/story.py` | Audio headers, historical mood/length fix, error messages |
| `backend/app/graph/llm.py` | Model switch to Sonnet, add max_tokens |
| `backend/app/graph/nodes/story_writer.py` | Add logging + transcript saving |
| `backend/app/graph/nodes/script_splitter.py` | Add logging |
| `backend/app/graph/nodes/voice_synthesizer.py` | Add logging |
| `backend/app/graph/nodes/audio_stitcher.py` | Add logging |
| `frontend/src/components/StoryScreen.tsx` | Player fixes (seeking, state sync, error handling) |
| `.gitignore` | Add `logs/` |

## Not In Scope

- Story validation/retry pipeline node (can add later if Sonnet quality is still insufficient)
- Player library replacement (custom fixes are sufficient)
- Database persistence (separate future effort)
- Playwright UI testing (will test manually after fixes)
