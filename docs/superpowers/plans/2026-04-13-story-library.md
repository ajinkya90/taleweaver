# Story Library — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let each user view and replay their past stories with audio from a personal library.

**Architecture:** Add a `BYTEA` column to the existing `stories` table for MP3 audio. New `/api/my-stories` endpoints return a user's own stories. New `MyStoriesScreen` component displays the library with audio playback and transcripts.

**Tech Stack:** asyncpg, FastAPI, React, TypeScript, Tailwind CSS 4

---

### Task 1: Add `audio_data` column and update `log_story()`

**Files:**
- Modify: `backend/app/db.py`

- [ ] **Step 1: Add column migration in `init_db()`**

In `backend/app/db.py`, after the `CREATE TABLE IF NOT EXISTS stories` block (after line 78), add:

```python
        # Add audio_data column if it doesn't exist (migration for existing tables)
        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'stories' AND column_name = 'audio_data'
                ) THEN
                    ALTER TABLE stories ADD COLUMN audio_data BYTEA;
                END IF;
            END $$;
        """)
```

- [ ] **Step 2: Update `log_story()` to accept and store audio_data**

Change the `log_story` function signature — add `audio_data: Optional[bytes] = None` parameter after `duration_seconds`:

```python
async def log_story(
    *,
    job_id: str,
    user_email: str,
    story_type: str,
    kid_name: str,
    kid_age: int,
    genre: Optional[str] = None,
    event_id: Optional[str] = None,
    description: Optional[str] = None,
    mood: Optional[str] = None,
    length: Optional[str] = None,
    prompt: str,
    title: str,
    story_text: str,
    duration_seconds: int,
    audio_data: Optional[bytes] = None,
) -> None:
```

Update the INSERT statement to include `audio_data`:

```python
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO stories (
                job_id, user_email, story_type, kid_name, kid_age,
                genre, event_id, description, mood, length,
                prompt, title, story_text, duration_seconds, audio_data
            ) VALUES (
                $1::uuid, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15
            )
            """,
            job_id, user_email, story_type, kid_name, kid_age,
            genre, event_id, description, mood, length,
            prompt, title, story_text, duration_seconds, audio_data,
        )
```

- [ ] **Step 3: Add user story query functions**

Add these functions at the end of `backend/app/db.py`:

```python
async def get_user_stories(user_email: str, limit: int = 20, offset: int = 0) -> list[dict]:
    """Paginated list of a user's stories (no audio_data, prompt, or story_text)."""
    if not _pool:
        return []
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, title, kid_name, kid_age, story_type, genre, event_id,
                   duration_seconds, created_at
            FROM stories
            WHERE user_email = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            user_email, limit, offset,
        )
        return [dict(row) for row in rows]


async def get_user_stories_count(user_email: str) -> int:
    """Total stories for a user."""
    if not _pool:
        return 0
    async with _pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM stories WHERE user_email = $1",
            user_email,
        )


async def get_user_story(story_id: int, user_email: str) -> Optional[dict]:
    """Full story detail for a user (no audio_data)."""
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, job_id, user_email, story_type, kid_name, kid_age,
                      genre, event_id, description, mood, length,
                      title, story_text, duration_seconds, created_at
               FROM stories WHERE id = $1 AND user_email = $2""",
            story_id, user_email,
        )
        return dict(row) if row else None


async def get_story_audio(story_id: int) -> Optional[bytes]:
    """Return raw audio bytes for a story, or None."""
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT audio_data FROM stories WHERE id = $1",
            story_id,
        )
```

- [ ] **Step 4: Run existing tests**

```bash
cd /Users/ajinkya/work/audio-story-creator/backend && source venv/bin/activate && python -m pytest tests/ -v
```

Expected: All existing tests still pass.

- [ ] **Step 5: Commit**

```bash
cd /Users/ajinkya/work/audio-story-creator && git add backend/app/db.py
git commit -m "feat: add audio_data column and user story query functions"
```

---

### Task 2: Pass audio bytes to `log_story()` in pipeline

**Files:**
- Modify: `backend/app/routes/story.py:139-156`

- [ ] **Step 1: Add `audio_data` to the `log_story` call**

In `backend/app/routes/story.py`, in the `run_pipeline` function, update the `log_story` call (around line 141-156) to include `audio_data`:

Add after the `duration_seconds` kwarg:

```python
                audio_data=final_state.get("final_audio", b""),
```

The full call becomes:

```python
            await log_story(
                job_id=job_id,
                user_email=user_email,
                story_type=state["story_type"],
                kid_name=state["kid_name"],
                kid_age=state["kid_age"],
                genre=state.get("genre"),
                event_id=state.get("event_id"),
                description=state.get("description"),
                mood=state.get("mood"),
                length=state.get("length"),
                prompt=final_state.get("prompt", ""),
                title=final_state["title"],
                story_text=final_state.get("story_text", ""),
                duration_seconds=final_state["duration_seconds"],
                audio_data=final_state.get("final_audio", b""),
            )
```

- [ ] **Step 2: Run tests**

```bash
cd /Users/ajinkya/work/audio-story-creator/backend && source venv/bin/activate && python -m pytest tests/ -v
```

- [ ] **Step 3: Commit**

```bash
cd /Users/ajinkya/work/audio-story-creator && git add backend/app/routes/story.py
git commit -m "feat: store audio bytes in database on story completion"
```

---

### Task 3: Create my_stories API routes

**Files:**
- Create: `backend/app/routes/my_stories.py`
- Modify: `backend/app/main.py` (register router)

- [ ] **Step 1: Create `backend/app/routes/my_stories.py`**

```python
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.db import (
    get_story_audio,
    get_user_stories,
    get_user_stories_count,
    get_user_story,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/my-stories")


def _get_user_email(request: Request) -> str:
    email = getattr(request.state, "user_email", "")
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return email


@router.get("")
async def list_my_stories(request: Request, limit: int = 20, offset: int = 0):
    email = _get_user_email(request)
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    stories = await get_user_stories(email, limit=limit, offset=offset)
    total = await get_user_stories_count(email)
    for s in stories:
        if s.get("created_at"):
            s["created_at"] = s["created_at"].isoformat()
    return {"stories": stories, "total": total, "limit": limit, "offset": offset}


@router.get("/{story_id}")
async def get_my_story(story_id: int, request: Request):
    email = _get_user_email(request)
    story = await get_user_story(story_id, email)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if story.get("created_at"):
        story["created_at"] = story["created_at"].isoformat()
    if story.get("job_id"):
        story["job_id"] = str(story["job_id"])
    return story


@router.get("/{story_id}/audio")
async def get_my_story_audio(story_id: int, request: Request):
    email = _get_user_email(request)
    # Verify ownership first
    story = await get_user_story(story_id, email)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    audio = await get_story_audio(story_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not available")
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="story-{story_id}.mp3"',
            "Content-Length": str(len(audio)),
        },
    )
```

- [ ] **Step 2: Register router in main.py**

In `backend/app/main.py`, add import:

```python
from app.routes.my_stories import router as my_stories_router
```

After `app.include_router(admin_router)`, add:

```python
app.include_router(my_stories_router)
```

- [ ] **Step 3: Add admin audio endpoint**

In `backend/app/routes/admin.py`, add import for `get_story_audio`:

```python
from app.db import (
    get_admin_emails,
    add_allowed_email,
    get_stories,
    get_stories_count,
    get_story,
    get_story_audio,
    list_allowed_emails,
    remove_allowed_email,
)
```

Add this endpoint at the end of the file:

```python
@router.get("/stories/{story_id}/audio")
async def admin_get_story_audio(story_id: int, request: Request):
    _require_admin(request)
    audio = await get_story_audio(story_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not available")
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="story-{story_id}.mp3"',
            "Content-Length": str(len(audio)),
        },
    )
```

Add `Response` to the fastapi imports at the top of admin.py:

```python
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
```

- [ ] **Step 4: Test server starts**

```bash
cd /Users/ajinkya/work/audio-story-creator/backend && source venv/bin/activate && python -c "from app.main import app; print('OK')"
```

- [ ] **Step 5: Commit**

```bash
cd /Users/ajinkya/work/audio-story-creator && git add backend/app/routes/my_stories.py backend/app/main.py backend/app/routes/admin.py
git commit -m "feat: add my-stories and admin audio API endpoints"
```

---

### Task 4: Add frontend types and API client functions

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Add types to `frontend/src/types/index.ts`**

Add at the end of the file:

```typescript

export interface MyStoryEntry {
  id: number;
  title: string;
  kid_name: string;
  kid_age: number;
  story_type: string;
  genre: string | null;
  event_id: string | null;
  duration_seconds: number;
  created_at: string;
}

export interface MyStoryDetail extends MyStoryEntry {
  story_text: string;
  mood: string | null;
  length: string | null;
  description: string | null;
}

export interface MyStoriesResponse {
  stories: MyStoryEntry[];
  total: number;
  limit: number;
  offset: number;
}
```

- [ ] **Step 2: Add API functions to `frontend/src/api/client.ts`**

Add the new types to the import at the top:

```typescript
import type {
  // ... existing types ...
  MyStoryDetail,
  MyStoriesResponse,
} from "../types";
```

Add these functions at the end of the file:

```typescript

// My Stories API

export async function fetchMyStories(limit = 20, offset = 0): Promise<MyStoriesResponse> {
  const res = await fetch(`${BASE}/my-stories?limit=${limit}&offset=${offset}`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export async function fetchMyStory(id: number): Promise<MyStoryDetail> {
  const res = await fetch(`${BASE}/my-stories/${id}`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export function getMyStoryAudioUrl(id: number): string {
  const token = getAuthToken();
  const url = `${BASE}/my-stories/${id}/audio`;
  if (token) return `${url}?token=${encodeURIComponent(token)}`;
  return url;
}
```

- [ ] **Step 3: Type check**

```bash
cd /Users/ajinkya/work/audio-story-creator/frontend && npx tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
cd /Users/ajinkya/work/audio-story-creator && git add frontend/src/types/index.ts frontend/src/api/client.ts
git commit -m "feat: add my-stories types and API client functions"
```

---

### Task 5: Build MyStoriesScreen component

**Files:**
- Create: `frontend/src/components/MyStoriesScreen.tsx`

- [ ] **Step 1: Create `frontend/src/components/MyStoriesScreen.tsx`**

```tsx
import { Fragment, useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import type { MyStoryEntry, MyStoryDetail } from "../types";
import {
  fetchMyStories,
  fetchMyStory,
  getMyStoryAudioUrl,
} from "../api/client";

interface MyStoriesScreenProps {
  onBack: () => void;
}

export default function MyStoriesScreen({ onBack }: MyStoriesScreenProps) {
  const [stories, setStories] = useState<MyStoryEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);
  const [detail, setDetail] = useState<MyStoryDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const limit = 20;

  const load = useCallback(async (off: number) => {
    setLoading(true);
    try {
      const data = await fetchMyStories(limit, off);
      setStories(data.stories);
      setTotal(data.total);
      setOffset(off);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load stories");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(0); }, [load]);

  const handleExpand = async (id: number) => {
    if (expanded === id) {
      setExpanded(null);
      setDetail(null);
      return;
    }
    setExpanded(id);
    setDetailLoading(true);
    try {
      const d = await fetchMyStory(id);
      setDetail(d);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading && stories.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 text-center">
        <p className="text-starlight/50">Loading your stories...</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h2
          className="text-2xl font-bold text-ethereal"
          style={{ fontFamily: "var(--font-display)" }}
        >
          My Stories
        </h2>
        <button
          onClick={onBack}
          className="text-starlight/50 hover:text-starlight transition-colors text-sm"
        >
          &larr; Create new story
        </button>
      </div>

      {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

      {stories.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card p-12 text-center"
        >
          <p className="text-starlight/40 text-lg mb-2">No stories yet</p>
          <p className="text-starlight/30 text-sm">
            Create your first story and it will appear here
          </p>
        </motion.div>
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
          {stories.map((s) => (
            <Fragment key={s.id}>
              <motion.div
                onClick={() => handleExpand(s.id)}
                className={`glass-card p-4 cursor-pointer transition-all duration-300 hover:shadow-[0_0_20px_rgba(124,58,237,0.2)] ${
                  expanded === s.id ? "border-purple-500/30" : ""
                }`}
                style={expanded === s.id ? { borderColor: "rgba(124,58,237,0.3)" } : {}}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-starlight font-semibold truncate">{s.title}</h3>
                    <p className="text-starlight/40 text-sm mt-1">
                      {s.kid_name}, age {s.kid_age}
                      <span className="mx-2">-</span>
                      {s.story_type === "custom" ? s.genre : s.event_id}
                    </p>
                  </div>
                  <div className="text-right ml-4 flex-shrink-0">
                    <p className="text-starlight/50 text-xs">
                      {new Date(s.created_at).toLocaleDateString()}
                    </p>
                    <p className="text-starlight/30 text-xs mt-1">
                      {Math.floor(s.duration_seconds / 60)}:{String(s.duration_seconds % 60).padStart(2, "0")}
                    </p>
                  </div>
                </div>
              </motion.div>

              {expanded === s.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="glass-card p-5 space-y-4"
                >
                  {detailLoading ? (
                    <p className="text-starlight/50 text-sm">Loading...</p>
                  ) : detail ? (
                    <>
                      {/* Audio player */}
                      <div>
                        <audio
                          controls
                          src={getMyStoryAudioUrl(s.id)}
                          className="w-full"
                          preload="none"
                        />
                      </div>

                      {/* Metadata */}
                      <div className="flex flex-wrap gap-3 text-xs text-starlight/40">
                        {detail.mood && <span>Mood: {detail.mood}</span>}
                        {detail.length && <span>Length: {detail.length}</span>}
                        <span>Duration: {detail.duration_seconds}s</span>
                      </div>

                      {/* Transcript */}
                      <div>
                        <h4 className="text-starlight/40 text-sm mb-2">Story</h4>
                        <pre className="text-starlight/80 whitespace-pre-wrap bg-black/20 rounded-lg p-4 max-h-80 overflow-y-auto text-sm leading-relaxed">
                          {detail.story_text}
                        </pre>
                      </div>
                    </>
                  ) : (
                    <p className="text-red-400 text-sm">Failed to load story details</p>
                  )}
                </motion.div>
              )}
            </Fragment>
          ))}

          {total > limit && (
            <div className="flex justify-center gap-2 pt-4">
              <button
                disabled={offset === 0}
                onClick={() => load(Math.max(0, offset - limit))}
                className="px-3 py-1 rounded text-sm text-starlight/50 hover:text-starlight disabled:opacity-30 transition-colors"
              >
                &larr; Prev
              </button>
              <span className="text-starlight/40 text-sm py-1">
                {offset + 1}&ndash;{Math.min(offset + limit, total)} of {total}
              </span>
              <button
                disabled={offset + limit >= total}
                onClick={() => load(offset + limit)}
                className="px-3 py-1 rounded text-sm text-starlight/50 hover:text-starlight disabled:opacity-30 transition-colors"
              >
                Next &rarr;
              </button>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Type check**

```bash
cd /Users/ajinkya/work/audio-story-creator/frontend && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
cd /Users/ajinkya/work/audio-story-creator && git add frontend/src/components/MyStoriesScreen.tsx
git commit -m "feat: add MyStoriesScreen component with audio playback"
```

---

### Task 6: Wire MyStoriesScreen into App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add imports**

Add `MyStoriesScreen` import:

```typescript
import MyStoriesScreen from "./components/MyStoriesScreen";
```

- [ ] **Step 2: Add state**

After the `showAdmin` state variable, add:

```typescript
  const [showMyStories, setShowMyStories] = useState(false);
```

- [ ] **Step 3: Add "My Stories" button in the header**

In the `<header>` section, after the subtitle `<p>` tag ("Where stories come alive"), and before the admin button block, add:

```tsx
          <button
            onClick={() => { setShowMyStories(!showMyStories); setShowAdmin(false); }}
            className="mt-2 text-sm text-ethereal/60 hover:text-ethereal transition-colors"
          >
            {showMyStories ? "Create Story" : "My Stories"}
          </button>
```

- [ ] **Step 4: Update the Taleweaver title click handler**

The title click handler currently calls `handleCreateAnother()` and sets step to "hero". Also close My Stories:

```tsx
            onClick={() => { handleCreateAnother(); setStep("hero"); setShowMyStories(false); setShowAdmin(false); }}
```

- [ ] **Step 5: Add MyStoriesScreen to the conditional rendering**

In the `<main>` section, update the existing conditional. Currently it's:

```tsx
{showAdmin ? (
  <AdminScreen ... />
) : (
  <AnimatePresence ...>
    ...
  </AnimatePresence>
)}
```

Change it to:

```tsx
{showAdmin ? (
  <AdminScreen onBack={() => setShowAdmin(false)} />
) : showMyStories ? (
  <MyStoriesScreen onBack={() => setShowMyStories(false)} />
) : (
  <AnimatePresence mode="wait">
    ...
  </AnimatePresence>
)}
```

- [ ] **Step 6: Type check and test**

```bash
cd /Users/ajinkya/work/audio-story-creator/frontend && npx tsc --noEmit
```

Start dev server and verify:
- "My Stories" button visible in header
- Clicking it shows MyStoriesScreen
- Clicking "Taleweaver" title goes back to main
- Empty state shows when no stories exist

- [ ] **Step 7: Commit**

```bash
cd /Users/ajinkya/work/audio-story-creator && git add frontend/src/App.tsx
git commit -m "feat: wire MyStoriesScreen into app with header toggle"
```

---

### Task 7: Add tests and update docs

**Files:**
- Create: `backend/tests/test_my_stories_routes.py`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Create backend tests**

Create `backend/tests/test_my_stories_routes.py` following the same auth mocking pattern used in `test_admin_routes.py`:

Test cases:
- `GET /api/my-stories` returns empty list for user with no stories
- `GET /api/my-stories` returns 401 for unauthenticated request
- `GET /api/my-stories/{id}` returns 404 for non-existent story
- `GET /api/my-stories/{id}/audio` returns 404 for non-existent story
- `GET /api/my-stories` validates limit/offset bounds
- `GET /api/my-stories/{id}` does not return another user's story

Read `backend/tests/test_admin_routes.py` for the auth mocking pattern (patching `_verify_google_token`, `db_get_allowed_emails`, and `settings.google_client_id`), then write equivalent tests for my-stories routes mocking `get_user_stories`, `get_user_stories_count`, `get_user_story`, and `get_story_audio`.

- [ ] **Step 2: Run all tests**

```bash
cd /Users/ajinkya/work/audio-story-creator/backend && source venv/bin/activate && python -m pytest tests/ -v
```

- [ ] **Step 3: Update CLAUDE.md**

Add the new endpoints to the API table:

```
| `/api/my-stories` | GET | List current user's stories (paginated) |
| `/api/my-stories/{id}` | GET | Full story detail for current user |
| `/api/my-stories/{id}/audio` | GET | Stream MP3 audio for current user's story |
| `/api/admin/stories/{id}/audio` | GET | Stream MP3 audio for any story (admin) |
```

- [ ] **Step 4: Commit and push**

```bash
cd /Users/ajinkya/work/audio-story-creator && git add backend/tests/test_my_stories_routes.py CLAUDE.md
git commit -m "test: add my-stories route tests and update docs"
git push origin main
```
