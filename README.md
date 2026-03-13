# Taleweaver

Personalized audio stories for kids, powered by AI.

Parents enter their child's name, age, and interests. Taleweaver writes a story with their kid as the protagonist, voices it with multiple characters, and delivers a downloadable MP3 - all in about 2-3 minutea.

**Two modes:**
- **Custom Story** - pick a genre, describe your idea, and the kid is the hero
- **Historical Adventure** - pick from 20 real historical events (including Indian history); the kid is an invisible time-traveling observer

Stories adapt to the child's age (3-12), use multi-voice narration, and are built on storytelling science (Story Spine structure, age-calibrated language, audio-first writing rules).

## Quick Start

### Using an AI coding agent (recommended)

If you have an AI coding agent (Claude Code, Cursor, Windsurf, etc.), give it this prompt:

> Run `./setup.sh` in the terminal and follow the interactive prompts. It will ask me which LLM provider I want and for my API keys. After setup completes, run `./start.sh` to start the app.

That's it. The setup script handles everything.
![Screenshot 2026-03-04 at 10 40 20 AM](https://github.com/user-attachments/assets/fd200c58-0481-430b-b0ad-d9f8c95fc77d)

![Screenshot 2026-03-12 at 9 39 04 AM](https://github.com/user-attachments/assets/7e79c78c-d31c-49c6-b001-4ba8a578f1f1)

![Screenshot 2026-03-12 at 9 39 34 AM](https://github.com/user-attachments/assets/cb300d2e-b611-4a3f-8f16-2e01b729a5fa)



### Manual setup

**Prerequisites:** Python 3.9+, Node.js 18+, npm, ffmpeg

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/audio-story-creator.git
cd audio-story-creator

# 2. Run the interactive setup
./setup.sh
```

The setup script will:
1. Check that prerequisites are installed
2. Ask you to choose an LLM provider (Groq, OpenAI, or Anthropic)
3. Ask for your API keys
4. Install all dependencies
5. Ask if you want local-only or WiFi access
6. Generate a `start.sh` script

Then start the app:

```bash
./start.sh
```

Open http://localhost:5173 (or your LAN IP if you chose WiFi access).

## Supported LLM Providers

| Provider | Model | Cost | Notes |
|----------|-------|------|-------|
| **Groq** | Llama 3.3 70B | Free tier available | Fast inference, good quality. [Get key](https://console.groq.com/keys) |
| **OpenAI** | GPT-4o | Paid | High quality stories. [Get key](https://platform.openai.com/api-keys) |
| **Anthropic** | Claude Sonnet 4.5 | Paid | High quality stories. [Get key](https://console.anthropic.com/settings/keys) |

**ElevenLabs** is required for text-to-speech (all providers). Free tier gives ~10 minutes of audio per month. [Get key](https://elevenlabs.io/app/settings/api-keys)

## WiFi Access (phones and tablets)

During setup, choose option 2 ("Local WiFi") to make Taleweaver accessible from any device on your network. The setup script auto-detects your local IP and configures everything.

Other devices can then open `http://<your-ip>:5173` in their browser.

## How It Works

```
[Parent Input] → [Story Writer] → [Script Splitter] → [Voice Synthesizer] → [Audio Stitcher] → [MP3]
                    (LLM)          (parse dialogue)     (ElevenLabs TTS)      (pydub + music)
```

1. **Story Writer** - LLM generates an age-appropriate story using storytelling science prompts
2. **Script Splitter** - parses the story into narrator/character segments, assigns voice types
3. **Voice Synthesizer** - ElevenLabs generates audio for each segment with different voices
4. **Audio Stitcher** - concatenates segments, adds pauses, mixes in mood-based background music

Jobs are async. The frontend polls for progress while the pipeline runs (~30-90 seconds).

## Project Structure

```
audio-story-creator/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings (reads .env)
│   │   ├── routes/              # API endpoints
│   │   ├── graph/               # LangGraph pipeline + nodes
│   │   ├── models/              # Pydantic request/response models
│   │   ├── prompts/             # LLM prompt engineering
│   │   └── data/                # Genres, historical events, background music
│   ├── tests/                   # Backend tests (94 tests, 98% coverage)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # 3-screen flow (hero → craft → story)
│   │   ├── components/          # HeroScreen, CraftScreen, StoryScreen
│   │   └── api/client.ts        # API client
│   └── package.json
├── setup.sh                     # Interactive setup script
├── docker-compose.yml           # Docker deployment (optional)
└── README.md
```

## Running Tests

```bash
# Backend (94 tests, 98% coverage)
cd backend
source venv/bin/activate
python -m pytest tests/ -v

# Frontend (47 tests)
cd frontend
npm test
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/genres` | GET | List 7 story genres |
| `/api/historical-events` | GET | List 20 curated historical events |
| `/api/story/custom` | POST | Create a custom story |
| `/api/story/historical` | POST | Create a historical adventure |
| `/api/story/status/{job_id}` | GET | Poll job progress |
| `/api/story/audio/{job_id}` | GET | Download completed audio |

## Docker Deployment

```bash
# Make sure backend/.env exists (run setup.sh first)
docker compose up --build
```

Access at http://localhost (port 80).

## Configuration

All config lives in `backend/.env`. You can re-run `./setup.sh` at any time to reconfigure.

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | `groq`, `openai`, or `anthropic` |
| `GROQ_API_KEY` | Groq API key (if using Groq) |
| `OPENAI_API_KEY` | OpenAI API key (if using OpenAI) |
| `ANTHROPIC_API_KEY` | Anthropic API key (if using Anthropic) |
| `ELEVENLABS_API_KEY` | ElevenLabs API key (required) |
| `NARRATOR_VOICE_ID` | ElevenLabs voice ID for narrator |
| `CHARACTER_MALE_VOICE_ID` | Voice ID for male characters |
| `CHARACTER_FEMALE_VOICE_ID` | Voice ID for female characters |
| `CHARACTER_CHILD_VOICE_ID` | Voice ID for child characters |

## Tech Stack

- **Backend:** Python, FastAPI, LangGraph, ElevenLabs TTS, pydub
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4, Framer Motion
- **LLM:** Groq (Llama 3.3) / OpenAI (GPT-4o) / Anthropic (Claude Sonnet 4.5)

## License

[MIT](LICENSE)
