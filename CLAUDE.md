# Audio Story Creator for Kids — Taleweaver

## Quick Start for New Sessions

When starting a new session, orient yourself with:

1. **Check git state**: `git status`, `git log --oneline -5` — see what branch you're on and recent changes
2. **Check deployments**:
   - Frontend (Vercel): `vercel ls | head -5` — latest deployment status
   - Backend (Render): use `mcp__render__list_services` (workspace auto-selects to "Tale Weaver") or check `https://taleweaver-api.onrender.com/api/health`
3. **Local dev**: backend runs on `:8000` (uvicorn), frontend on `:5173` (vite) — frontend proxies `/api` to backend
4. **Key files for context**: `backend/app/main.py`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`

Important things to know:
- The GitHub repo is `ajinkya90/taleweaver` but the local directory is `audio-story-creator`
- Frontend deploys to Vercel, backend deploys to Render — both auto-deploy on push to `main`
- Do NOT run `vercel link` at the repo root — it auto-detects the monorepo and creates duplicate projects
- Do NOT create a `vercel.json` at the repo root for the same reason
- Render MCP tools require workspace selection first — the workspace is "Tale Weaver" (`tea-d7d90uflk1mc73ekc470`)

## What This Is

A web app where parents create personalized audio stories for their kids. Two modes:
1. **Custom Story** — parent picks a genre + writes a short description. The kid is the protagonist.
2. **Historical Adventure** — parent picks from 20 curated historical events (including Indian history). The kid is a silent time-traveling observer (preserves historical accuracy).

Stories are age-adaptive (3-12 years), use multi-voice narration (narrator + character voices), include mood-based background music, and download as MP3.

## Tech Stack

- **Backend**: Python 3.9+, FastAPI, LangGraph, ElevenLabs TTS
- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS 4, framer-motion
- **LLM**: Claude Haiku (default), also supports Groq and OpenAI (configurable via `LLM_PROVIDER` env var)
- **TTS**: ElevenLabs with 4 pre-configured voices (narrator [Rachel/female], male, female, child)
- **Audio processing**: pydub (requires ffmpeg) — stitches voice segments + mood-based background music
- **Fonts**: Google Fonts — Cinzel (display headings) + Inter (body text)

## Project Structure

```
audio-story-creator/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, router registration
│   │   ├── config.py            # Pydantic settings (reads .env)
│   │   ├── routes/
│   │   │   ├── config.py        # GET /api/genres, GET /api/historical-events
│   │   │   └── story.py         # POST /api/story/custom, /historical, GET /status, /audio
│   │   ├── graph/
│   │   │   ├── llm.py           # Configurable LLM provider (anthropic/groq/openai)
│   │   │   ├── pipeline.py      # LangGraph StateGraph assembly
│   │   │   ├── state.py         # StoryState and Segment TypedDicts
│   │   │   └── nodes/
│   │   │       ├── story_writer.py      # Generates story text via LLM
│   │   │       ├── script_splitter.py   # Parses into narrator/character segments
│   │   │       ├── voice_synthesizer.py # ElevenLabs TTS per segment
│   │   │       └── audio_stitcher.py    # Concatenates MP3 segments + mixes background music
│   │   ├── models/
│   │   │   ├── requests.py      # KidProfile, CustomStoryRequest, HistoricalStoryRequest (+ mood, length fields)
│   │   │   └── responses.py     # Job responses (created, status, complete, error)
│   │   ├── data/
│   │   │   ├── genres.yaml      # 7 genres (adventure, fantasy, bedtime, funny, space, underwater, magical-forest)
│   │   │   ├── historical_events.yaml  # 20 events with key_facts for LLM grounding
│   │   │   └── music/           # Background music files (per mood)
│   │   │       ├── exciting.mp3
│   │   │       ├── heartwarming.mp3
│   │   │       ├── funny.mp3
│   │   │       ├── mysterious.mp3
│   │   │       └── default.mp3
│   │   └── prompts/
│   │       ├── custom_story.py      # Storytelling-science prompts (Story Spine, age-calibrated, audio rules)
│   │       └── historical_story.py  # Same approach, enforcing silent observer + accuracy
│   ├── tests/
│   ├── requirements.txt
│   ├── .env                     # API keys (not committed)
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # 3-screen immersive flow (hero → craft → story)
│   │   ├── components/
│   │   │   ├── HeroScreen.tsx          # Landing screen with app title and "Begin" CTA
│   │   │   ├── CraftScreen.tsx         # Story creation: kid profile, story type, genre/event, mood, length
│   │   │   ├── StoryScreen.tsx         # Generation progress + audio playback/download
│   │   │   └── ParticleBackground.tsx  # Floating particle animation overlay
│   │   ├── api/client.ts        # All API calls to backend
│   │   └── types/index.ts       # TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts           # Tailwind plugin + /api proxy to :8000
└── docs/plans/
    ├── 2026-03-01-audio-story-creator-design.md
    ├── 2026-03-01-audio-story-creator-plan.md
    ├── 2026-03-02-storyforge-v2-design.md
    └── 2026-03-02-taleweaver-v2-plan.md
```

## Running Locally

```bash
# Backend (terminal 1)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend
npm run dev
```

Open http://localhost:5173

### LAN access (other devices on same WiFi)

```bash
# Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
npx vite --host 0.0.0.0 --port 5173
```

Access via `http://<your-local-ip>:5173`

## Running Tests

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Health check |
| `/api/genres` | GET | List story genres |
| `/api/historical-events` | GET | List curated historical events (20) |
| `/api/story/custom` | POST | Create custom story job (accepts mood + length) |
| `/api/story/historical` | POST | Create historical story job (accepts mood + length) |
| `/api/story/status/{job_id}` | GET | Poll job progress |
| `/api/story/audio/{job_id}` | GET | Download completed audio |
| `/api/admin/me` | GET | Check if current user is admin |
| `/api/admin/emails` | GET | List allowed emails (admin only) |
| `/api/admin/emails` | POST | Add email to allowlist (admin only) |
| `/api/admin/emails/{email}` | DELETE | Remove email from allowlist (admin only) |
| `/api/admin/stories` | GET | Paginated story log (admin only) |
| `/api/admin/stories/{id}` | GET | Full story detail with prompt (admin only) |
| `/api/admin/stories/{id}/audio` | GET | Stream MP3 audio for any story (admin) |
| `/api/my-stories` | GET | List current user's stories (paginated) |
| `/api/my-stories/{id}` | GET | Full story detail for current user |
| `/api/my-stories/{id}/audio` | GET | Stream MP3 audio for current user's story |

## LangGraph Pipeline

```
[Input] → [Story Writer] → [Script Splitter] → [Voice Synthesizer] → [Audio Stitcher] → [Output]
```

- Jobs are async — POST returns a `job_id`, frontend polls `/status/{job_id}` every 2 seconds
- Jobs stored in-memory (lost on server restart)
- Typical generation time: 20-90 seconds depending on story length
- Audio stitcher mixes mood-based background music under narration

## Key Design Decisions

- **Kid as silent observer** in historical stories to preserve accuracy
- **Age-adaptive content**: ages 3-5 get simple/short stories (~200-300 words), 6-8 moderate (~400-600), 9-12 rich/complex (~700-1000)
- **Multi-voice narration**: script splitter assigns voice types (narrator/male/female/child) based on character names
- **Female narrator voice** (Rachel) as the default narrator
- **Mood and length controls**: exciting/heartwarming/funny/mysterious moods; short/medium/long lengths
- **Background music mixing**: audio stitcher layers mood-matched music under the narrated story
- **Storytelling-science prompts**: Story Spine structure, age-calibrated directives, audio-specific storytelling rules
- **Job-based polling** instead of streaming — generation takes too long for a single request
- **3-screen immersive UI**: dark fantasy theme with glassmorphism, particle effects, and glow effects (replaces v1 6-step wizard)
- **CORS allows all origins** for LAN access

## Deployment

### GitHub Repo
- **Repo**: `github.com/ajinkya90/taleweaver` (local dir is `audio-story-creator`)
- **Branch**: `main` — both services auto-deploy on every push to main
- **No path filtering** — any push triggers both frontend and backend deploys, even if changes are unrelated

### Frontend — Vercel
- **Project**: `frontend` (Vercel team: `ajinkya90-7765s-projects`)
- **Root Directory**: `frontend` (set in Vercel dashboard)
- **Framework**: Vite
- **Build Command**: `vite build`
- **Production URL**: `https://frontend-ajinkya90-7765s-projects.vercel.app`
- **Env vars** (set in Vercel dashboard): `VITE_GOOGLE_CLIENT_ID`, `VITE_API_URL`
- `VITE_API_URL` points to the Render backend URL

### Backend — Render
- **Service**: `taleweaver-api` (Web Service, Starter plan, Oregon region)
- **Runtime**: Python
- **Root Directory**: not set — build/start commands `cd backend` explicitly
- **Build Command**: `cd backend && pip install -r requirements.txt` + installs ffmpeg from static binary
- **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 10000`
- **Production URL**: `https://taleweaver-api.onrender.com`
- **Env vars**: set in Render dashboard (API keys for LLM, ElevenLabs, voice IDs, Google OAuth)
- **Note**: Render free/starter tier spins down after inactivity — first request after idle has a cold start

### Database — Render Postgres
- **Instance**: `taleweaver-db` (free tier, Oregon)
- **Tables**: `allowed_emails` (email allowlist, replaces ALLOWED_EMAILS env var), `stories` (logs every generated story with full prompt and text)
- **Library**: asyncpg (connection pool, tables auto-created on startup)
- **Admin**: users in `ADMIN_EMAILS` env var can access `/api/admin/*` endpoints and the admin UI

### Deployment gotchas
- Do NOT create a `vercel.json` at the repo root — Vercel's `vercel link` auto-detects the monorepo and tries to create a second project with `experimentalServices`, which causes duplicate deployments
- The `.vercel` directories (root and `frontend/`) are gitignored — local project links only
- Backend env vars live in Render, frontend env vars (VITE_*) live in Vercel — they are NOT shared

## Environment Variables

### Backend (Render dashboard)
```
DATABASE_URL=                    # Auto-set by Render when linking Postgres
ADMIN_EMAILS=                    # Comma-separated admin email addresses
LLM_PROVIDER=anthropic          # anthropic, groq, or openai
ANTHROPIC_API_KEY=               # Required if using anthropic
GROQ_API_KEY=                    # Required if using groq
OPENAI_API_KEY=                  # Required if using openai
ELEVENLABS_API_KEY=              # Always required for TTS
NARRATOR_VOICE_ID=               # ElevenLabs voice IDs (Rachel/female for narrator)
CHARACTER_MALE_VOICE_ID=
CHARACTER_FEMALE_VOICE_ID=
CHARACTER_CHILD_VOICE_ID=
```

### Frontend (Vercel dashboard)
```
VITE_API_URL=                    # Render backend URL (e.g. https://taleweaver-api.onrender.com)
VITE_GOOGLE_CLIENT_ID=           # Google OAuth client ID for Sign-In
```

## What's Not Built Yet (future ideas)

- User accounts and saved story library
- Edge TTS as free alternative to ElevenLabs
- Story sharing (link or QR code)
- Story illustrations generated with an image model
- Content moderation beyond LLM system prompt guardrails
- Rate limiting
