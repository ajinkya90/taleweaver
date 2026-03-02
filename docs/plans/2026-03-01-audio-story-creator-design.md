# Audio Story Creator for Kids — Design Document

## Overview

A web application where parents create personalized audio stories for their kids. The child becomes a character in the story. Two modes: custom stories (guided prompt builder) and historical adventures (kid as silent observer of real events).

## Tech Stack

- **Backend**: FastAPI + LangGraph + ElevenLabs TTS
- **Frontend**: React (Vite) + TypeScript
- **LLM**: Configurable (Groq, OpenAI, or Anthropic) via environment variable

## User Flow

### Step 1: Kid's Profile
- Name (required), Age (required, 3-12)
- Optional: favorite animal, favorite color, hobby, best friend's name, pet's name, personality (shy/adventurous/curious/funny)

### Step 2: Story Type Selection
- **Custom Story**: Parent picks a genre (Adventure, Fantasy, Bedtime, Funny, Space, Underwater, Magical Forest) and writes a short description
- **Historical Adventure**: Parent picks from a curated list of historical events. Kid is a silent observer to preserve historical accuracy.

### Step 3: Generation
- Animated waiting screen with progress indicators per stage (writing → recording voices → finishing up)

### Step 4: Listen & Download
- Audio player with play/pause/seek
- Download as MP3
- "Create Another Story" button

## Architecture

```
┌─────────────────────────────────┐
│        React (Vite) Frontend    │
│  - Story creation wizard        │
│  - Audio player                 │
│  - Kid profile form             │
└──────────────┬──────────────────┘
               │ REST API
┌──────────────▼──────────────────┐
│        FastAPI Backend          │
│  - /api/story/custom            │
│  - /api/story/historical        │
│  - /api/genres                  │
│  - /api/historical-events       │
└──────────┬──────────┬───────────┘
           │          │
    ┌──────▼──┐  ┌────▼──────────┐
    │LangGraph│  │  ElevenLabs   │
    │  (LLM)  │  │    (TTS)      │
    └─────────┘  └───────────────┘
```

Frontend runs on port 5173, backend on port 8000.

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/genres` | GET | Returns list of genres for custom stories |
| `/api/historical-events` | GET | Returns curated historical events list |
| `/api/story/custom` | POST | Generate a custom story |
| `/api/story/historical` | POST | Generate a historical story |
| `/api/story/status/{job_id}` | GET | Poll generation progress |
| `/api/story/audio/{job_id}` | GET | Download final audio file |

Job-based polling approach — story generation + multi-voice TTS takes 30-90 seconds.

## LangGraph Pipeline

```
[Input] → [Story Writer] → [Script Splitter] → [Voice Synthesizer] → [Audio Stitcher] → [Output]
```

1. **Story Writer**: Takes kid profile + genre/prompt or historical event. Generates age-appropriate story text. System prompt enforces kid as character (custom) or silent observer (historical).
2. **Script Splitter**: Parses story into segments — `{speaker: "narrator" | "character_name", text: "..."}`.
3. **Voice Synthesizer**: Sends each segment to ElevenLabs with mapped voice ID. Runs segments in parallel.
4. **Audio Stitcher**: Concatenates audio segments into one MP3 with brief pauses between segments.
5. **Output**: Returns final MP3 + metadata (title, duration, character list).

### Voice Mapping
- Narrator: One warm storytelling voice (pre-selected ElevenLabs voice)
- Characters: 3-4 pre-selected distinct voices (male/female/child). Script Splitter assigns voices based on character type.

## Data Models

### Request: Custom Story
```json
{
  "kid": {
    "name": "Arjun",
    "age": 7,
    "favorite_animal": "tiger",
    "favorite_color": "blue",
    "hobby": "drawing",
    "best_friend": "Riya",
    "pet_name": "Bruno",
    "personality": "adventurous"
  },
  "genre": "fantasy",
  "description": "A magical paintbrush that brings drawings to life"
}
```

### Request: Historical Story
```json
{
  "kid": {
    "name": "Arjun",
    "age": 7
  },
  "event_id": "shivaji-agra-escape"
}
```

### Historical Events Config (YAML)
```yaml
- id: shivaji-agra-escape
  title: "Shivaji Maharaj's Great Escape from Agra"
  figure: "Chhatrapati Shivaji Maharaj"
  year: 1666
  summary: "How the Maratha king outsmarted the Mughal emperor..."
  key_facts:
    - "Shivaji was held under house arrest by Aurangzeb"
    - "Escaped by hiding in fruit baskets"
    - "Traveled in disguise back to Maharashtra"
  thumbnail: "shivaji-escape.webp"
```

### Response: Job Created
```json
{
  "job_id": "abc-123",
  "status": "processing",
  "stages": ["writing", "splitting", "synthesizing", "stitching"],
  "current_stage": "writing"
}
```

### Response: Status Poll
```json
{
  "job_id": "abc-123",
  "status": "processing",
  "current_stage": "synthesizing",
  "progress": 3,
  "total_segments": 8
}
```

### Response: Audio Ready
```json
{
  "job_id": "abc-123",
  "status": "complete",
  "title": "Arjun and the Magical Paintbrush",
  "duration_seconds": 285,
  "audio_url": "/api/story/audio/abc-123"
}
```

## Error Handling (v1)

- **LLM/ElevenLabs API failure**: Retry once, then return error to frontend
- **Rate limits/quota**: Clear error message to user
- **Inappropriate prompt**: LLM system prompt guardrails for kid-safe content
- **Job timeout**: 3-minute timeout, mark as failed
- **Job not found**: 404 on status/audio endpoints

### Not in v1
- No auth, no rate limiting per user
- No persistent storage — jobs live in memory
- No content moderation beyond LLM system prompt guardrails

## Project Structure

```
audio-story-creator/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── story.py
│   │   │   └── config.py
│   │   ├── graph/
│   │   │   ├── pipeline.py
│   │   │   ├── nodes/
│   │   │   │   ├── story_writer.py
│   │   │   │   ├── script_splitter.py
│   │   │   │   ├── voice_synthesizer.py
│   │   │   │   └── audio_stitcher.py
│   │   │   └── state.py
│   │   ├── models/
│   │   │   ├── requests.py
│   │   │   └── responses.py
│   │   ├── data/
│   │   │   ├── genres.yaml
│   │   │   └── historical_events.yaml
│   │   ├── prompts/
│   │   │   ├── custom_story.py
│   │   │   └── historical_story.py
│   │   └── config.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── KidProfileForm.tsx
│   │   │   ├── StoryTypeSelector.tsx
│   │   │   ├── CustomStoryForm.tsx
│   │   │   ├── HistoricalEventPicker.tsx
│   │   │   ├── GeneratingScreen.tsx
│   │   │   └── AudioPlayer.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   └── types/
│   │       └── index.ts
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Key Design Decisions

1. **Kid as silent observer in historical stories** — preserves accuracy
2. **Age-adaptive content** — vocabulary, length, complexity adjust to age range
3. **Multi-voice narration** — narrator + character voices via ElevenLabs for immersion
4. **Job-based polling** — handles long generation times (30-90s) gracefully
5. **Stateless v1** — no accounts, no persistence, generate and download
6. **Curated historical events** — quality over quantity, with key_facts to ground the LLM
7. **Guided prompt builder** — genre selection + description, not free-form
