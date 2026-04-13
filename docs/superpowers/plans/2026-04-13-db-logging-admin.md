# Database Logging + Admin Panel — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Postgres-backed story logging and email allowlist management with an admin UI.

**Architecture:** New `app/db.py` handles all DB operations via asyncpg. The auth middleware switches from env-var allowlist to DB queries. A new `/api/admin/*` router serves admin endpoints protected by an `ADMIN_EMAILS` check. The React frontend gets an `AdminScreen` component with tabs for emails and story logs, accessible only to admin users.

**Tech Stack:** asyncpg, FastAPI, React, TypeScript, Tailwind CSS 4

---

### Task 1: Provision Render Postgres + Add asyncpg dependency

**Files:**
- Modify: `backend/requirements.txt:16` (add asyncpg before pytest)
- Modify: `backend/.env.example:1-2` (add DATABASE_URL and ADMIN_EMAILS)
- Modify: `backend/app/config.py:15-17` (add database_url and admin_emails fields)

- [ ] **Step 1: Create Render Postgres instance**

Use the Render MCP tool:
```
mcp__render__create_postgres(name="taleweaver-db", plan="free", region="oregon")
```

After creation, link it to the `taleweaver-api` service in the Render dashboard so `DATABASE_URL` is auto-injected.

- [ ] **Step 2: Add asyncpg to requirements.txt**

Add after `google-auth==2.38.0` line (line 15), before the test dependencies:

```
asyncpg==0.30.0
```

- [ ] **Step 3: Add config fields**

In `backend/app/config.py`, add these fields to the `Settings` class after `allowed_emails`:

```python
    database_url: str = ""  # Postgres connection string
    admin_emails: str = ""  # Comma-separated admin email addresses
```

- [ ] **Step 4: Add to .env.example**

Add at the top of `backend/.env.example`:

```
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Admin
ADMIN_EMAILS=your-admin@gmail.com
```

- [ ] **Step 5: Install locally and commit**

```bash
cd backend && source venv/bin/activate && pip install asyncpg==0.30.0
git add backend/requirements.txt backend/.env.example backend/app/config.py
git commit -m "feat: add asyncpg dependency and DB config fields"
```

---

### Task 2: Create `app/db.py` — database module

**Files:**
- Create: `backend/app/db.py`
- Test: `backend/tests/test_db.py`

- [ ] **Step 1: Write tests for db module**

Create `backend/tests/test_db.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.db import _parse_emails, _get_admin_emails


def test_parse_emails_basic():
    assert _parse_emails("a@b.com, c@d.com") == {"a@b.com", "c@d.com"}


def test_parse_emails_empty():
    assert _parse_emails("") == set()
    assert _parse_emails(None) == set()


def test_parse_emails_whitespace_and_case():
    assert _parse_emails("  A@B.COM , c@d.com  ") == {"a@b.com", "c@d.com"}


def test_get_admin_emails():
    with patch("app.db.settings") as mock_settings:
        mock_settings.admin_emails = "admin@test.com, boss@test.com"
        result = _get_admin_emails()
        assert result == {"admin@test.com", "boss@test.com"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_db.py -v
```

Expected: FAIL — `app.db` module does not exist yet.

- [ ] **Step 3: Create `app/db.py`**

```python
import logging
from typing import Optional

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

pool: Optional[asyncpg.Pool] = None


def _parse_emails(raw: Optional[str]) -> set[str]:
    if not raw:
        return set()
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _get_admin_emails() -> set[str]:
    return _parse_emails(settings.admin_emails)


async def init_db():
    global pool
    if not settings.database_url:
        logger.warning("DATABASE_URL not set — database features disabled")
        return

    pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)

    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS allowed_emails (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                added_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id SERIAL PRIMARY KEY,
                job_id UUID NOT NULL,
                user_email TEXT NOT NULL,
                story_type TEXT NOT NULL,
                kid_name TEXT NOT NULL,
                kid_age INTEGER NOT NULL,
                genre TEXT,
                event_id TEXT,
                description TEXT,
                mood TEXT,
                length TEXT,
                prompt TEXT NOT NULL,
                title TEXT NOT NULL,
                story_text TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

    # Seed from env var if table is empty
    allowed_env = _parse_emails(settings.allowed_emails)
    if allowed_env:
        async with pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM allowed_emails")
            if count == 0:
                for email in allowed_env:
                    await conn.execute(
                        "INSERT INTO allowed_emails (email) VALUES ($1) ON CONFLICT DO NOTHING",
                        email,
                    )
                logger.info(f"Seeded {len(allowed_env)} emails from ALLOWED_EMAILS env var")

    logger.info("Database initialized")


async def close_db():
    global pool
    if pool:
        await pool.close()
        pool = None
        logger.info("Database pool closed")


async def get_allowed_emails() -> set[str]:
    if not pool:
        # Fallback to env var if DB is not configured
        return _parse_emails(settings.allowed_emails)
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT email FROM allowed_emails")
        return {row["email"] for row in rows}


async def add_allowed_email(email: str) -> bool:
    if not pool:
        return False
    email = email.strip().lower()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO allowed_emails (email) VALUES ($1)", email
            )
            return True
        except asyncpg.UniqueViolationError:
            return False


async def remove_allowed_email(email: str) -> bool:
    if not pool:
        return False
    email = email.strip().lower()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM allowed_emails WHERE email = $1", email
        )
        return result == "DELETE 1"


async def list_allowed_emails() -> list[dict]:
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, email, added_at FROM allowed_emails ORDER BY added_at DESC"
        )
        return [dict(row) for row in rows]


async def log_story(
    job_id: str,
    user_email: str,
    story_type: str,
    kid_name: str,
    kid_age: int,
    genre: Optional[str],
    event_id: Optional[str],
    description: Optional[str],
    mood: Optional[str],
    length: Optional[str],
    prompt: str,
    title: str,
    story_text: str,
    duration_seconds: int,
) -> None:
    if not pool:
        return
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO stories
               (job_id, user_email, story_type, kid_name, kid_age, genre, event_id,
                description, mood, length, prompt, title, story_text, duration_seconds)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)""",
            job_id, user_email, story_type, kid_name, kid_age, genre, event_id,
            description, mood, length, prompt, title, story_text, duration_seconds,
        )


async def get_stories(limit: int = 20, offset: int = 0) -> list[dict]:
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, job_id, user_email, story_type, kid_name, kid_age,
                      genre, event_id, description, mood, length, title,
                      duration_seconds, created_at
               FROM stories ORDER BY created_at DESC LIMIT $1 OFFSET $2""",
            limit, offset,
        )
        return [dict(row) for row in rows]


async def get_stories_count() -> int:
    if not pool:
        return 0
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM stories")


async def get_story(story_id: int) -> Optional[dict]:
    if not pool:
        return None
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM stories WHERE id = $1", story_id)
        return dict(row) if row else None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_db.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db.py backend/tests/test_db.py
git commit -m "feat: add database module with asyncpg"
```

---

### Task 3: Wire DB into FastAPI lifecycle + switch allowlist to DB

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add DB lifecycle to main.py**

Replace the import section and add lifespan. In `backend/app/main.py`:

Add import at the top (after existing imports around line 12-13):

```python
from contextlib import asynccontextmanager
from app.db import init_db, close_db, get_allowed_emails as db_get_allowed_emails, _get_admin_emails
```

Add lifespan before the `app = FastAPI(...)` line:

```python
@asynccontextmanager
async def lifespan(app):
    await init_db()
    yield
    await close_db()
```

Change the FastAPI constructor to:

```python
app = FastAPI(title="Taleweaver", lifespan=lifespan)
```

- [ ] **Step 2: Replace env-var allowlist with DB query**

Replace the `_get_allowed_emails()` function (lines 31-34) and update the middleware.

Delete the old `_get_allowed_emails` function.

In the `check_auth` middleware, replace the allowlist check block (lines 66-74) with:

```python
            email = payload.get("email", "").lower()
            allowed = await db_get_allowed_emails()
            if allowed:
                if email not in allowed:
                    return JSONResponse(status_code=403, content={"detail": "Email not authorized"})
            else:
                logger.warning(f"Google login by {email} rejected: no emails in allowlist")
                return JSONResponse(status_code=403, content={"detail": "No users authorized."})
            request.state.user_email = email
            return await call_next(request)
```

- [ ] **Step 3: Test locally**

```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

Check that `GET http://localhost:8000/api/health` returns `{"status": "ok"}`.
The server should log "DATABASE_URL not set — database features disabled" (expected for local dev without Postgres).

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: wire DB lifecycle and switch allowlist to database"
```

---

### Task 4: Thread prompt and user_email through the pipeline

**Files:**
- Modify: `backend/app/graph/state.py:27` (add prompt field)
- Modify: `backend/app/graph/nodes/story_writer.py:98` (return prompt in output)
- Modify: `backend/app/routes/story.py:107-142` (pass user_email, call log_story)

- [ ] **Step 1: Add `prompt` to StoryState**

In `backend/app/graph/state.py`, add after the `title: str` line (line 27):

```python
    prompt: str
```

- [ ] **Step 2: Return prompt from story_writer**

In `backend/app/graph/nodes/story_writer.py`, change the return statement on line 99 from:

```python
    return {"story_text": story_text, "title": title}
```

to:

```python
    return {"story_text": story_text, "title": title, "prompt": prompt}
```

- [ ] **Step 3: Add prompt to initial state in story.py**

In `backend/app/routes/story.py`, add `"prompt": ""` to both state dicts.

In the custom story state dict (around line 168), add after `"duration_seconds": 0,`:

```python
        "prompt": "",
```

In the historical story state dict (around line 219), add after `"duration_seconds": 0,`:

```python
        "prompt": "",
```

- [ ] **Step 4: Pass user_email into run_pipeline and log to DB**

In `backend/app/routes/story.py`, add import at the top:

```python
from app.db import log_story
```

Change the `run_pipeline` function signature (line 107) from:

```python
async def run_pipeline(job_id: str, state: dict):
```

to:

```python
async def run_pipeline(job_id: str, state: dict, user_email: str = ""):
```

After `jobs[job_id]["transcript"] = final_state.get("story_text", "")` (line 136), add:

```python
        # Log to database
        try:
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
            )
        except Exception as e:
            logger.error(f"[{job_id}] Failed to log story to DB: {e}")
```

- [ ] **Step 5: Pass user_email from request to run_pipeline**

In both `create_custom_story` and `create_historical_story` endpoints, extract user_email from request and pass it.

Add `Request` to the FastAPI import (already imported in main.py, but needed in story.py):

```python
from fastapi import APIRouter, HTTPException, Request
```

Change `create_custom_story` signature (line 146) from:

```python
async def create_custom_story(request: CustomStoryRequest):
```

to:

```python
async def create_custom_story(body: CustomStoryRequest, request: Request):
```

Update all references to `request.kid`, `request.genre`, etc. to use `body.kid`, `body.genre`, etc. throughout the function.

Change the `asyncio.create_task` call to pass user_email:

```python
    user_email = getattr(request.state, "user_email", "")
    task = asyncio.create_task(run_pipeline(job_id, state, user_email))
```

Do the same for `create_historical_story` — change signature from:

```python
async def create_historical_story(request: HistoricalStoryRequest):
```

to:

```python
async def create_historical_story(body: HistoricalStoryRequest, request: Request):
```

Update all references from `request.kid`, `request.event_id`, `request.mood`, `request.length` to `body.kid`, `body.event_id`, `body.mood`, `body.length`.

Pass user_email:

```python
    user_email = getattr(request.state, "user_email", "")
    task = asyncio.create_task(run_pipeline(job_id, state, user_email))
```

- [ ] **Step 6: Run existing tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All existing tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app/graph/state.py backend/app/graph/nodes/story_writer.py backend/app/routes/story.py
git commit -m "feat: thread prompt and user_email through pipeline for DB logging"
```

---

### Task 5: Create admin API routes

**Files:**
- Create: `backend/app/routes/admin.py`
- Modify: `backend/app/main.py` (register admin router)

- [ ] **Step 1: Create `backend/app/routes/admin.py`**

```python
import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.db import (
    _get_admin_emails,
    add_allowed_email,
    get_stories,
    get_stories_count,
    get_story,
    list_allowed_emails,
    remove_allowed_email,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin")


def _require_admin(request: Request) -> str:
    email = getattr(request.state, "user_email", "")
    if not email or email not in _get_admin_emails():
        raise HTTPException(status_code=403, detail="Admin access required")
    return email


class AddEmailRequest(BaseModel):
    email: str


@router.get("/me")
async def admin_me(request: Request):
    email = getattr(request.state, "user_email", "")
    is_admin = email in _get_admin_emails() if email else False
    return {"email": email, "is_admin": is_admin}


@router.get("/emails")
async def admin_list_emails(request: Request):
    _require_admin(request)
    emails = await list_allowed_emails()
    # Convert datetime to string for JSON serialization
    for e in emails:
        if e.get("added_at"):
            e["added_at"] = e["added_at"].isoformat()
    return {"emails": emails}


@router.post("/emails")
async def admin_add_email(body: AddEmailRequest, request: Request):
    _require_admin(request)
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")
    added = await add_allowed_email(email)
    if not added:
        raise HTTPException(status_code=409, detail="Email already exists")
    return {"email": email, "status": "added"}


@router.delete("/emails/{email}")
async def admin_remove_email(email: str, request: Request):
    _require_admin(request)
    removed = await remove_allowed_email(email)
    if not removed:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"email": email, "status": "removed"}


@router.get("/stories")
async def admin_list_stories(request: Request, limit: int = 20, offset: int = 0):
    _require_admin(request)
    stories = await get_stories(limit=min(limit, 100), offset=offset)
    total = await get_stories_count()
    # Convert datetime and UUID for JSON serialization
    for s in stories:
        if s.get("created_at"):
            s["created_at"] = s["created_at"].isoformat()
        if s.get("job_id"):
            s["job_id"] = str(s["job_id"])
    return {"stories": stories, "total": total, "limit": limit, "offset": offset}


@router.get("/stories/{story_id}")
async def admin_get_story(story_id: int, request: Request):
    _require_admin(request)
    story = await get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if story.get("created_at"):
        story["created_at"] = story["created_at"].isoformat()
    if story.get("job_id"):
        story["job_id"] = str(story["job_id"])
    return story
```

- [ ] **Step 2: Register admin router in main.py**

In `backend/app/main.py`, add import:

```python
from app.routes.admin import router as admin_router
```

After `app.include_router(story_router)` (line 90), add:

```python
app.include_router(admin_router)
```

- [ ] **Step 3: Test server starts**

```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

Verify `GET http://localhost:8000/api/admin/me` returns `{"email": "", "is_admin": false}` (no auth in local dev without Google).

- [ ] **Step 4: Commit**

```bash
git add backend/app/routes/admin.py backend/app/main.py
git commit -m "feat: add admin API routes for email and story management"
```

---

### Task 6: Add admin API functions to frontend client

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Add admin types**

In `frontend/src/types/index.ts`, add at the end of the file:

```typescript

export interface AdminMe {
  email: string;
  is_admin: boolean;
}

export interface AllowedEmail {
  id: number;
  email: string;
  added_at: string;
}

export interface StoryLogEntry {
  id: number;
  job_id: string;
  user_email: string;
  story_type: string;
  kid_name: string;
  kid_age: number;
  genre: string | null;
  event_id: string | null;
  description: string | null;
  mood: string | null;
  length: string | null;
  title: string;
  duration_seconds: number;
  created_at: string;
}

export interface StoryDetail extends StoryLogEntry {
  prompt: string;
  story_text: string;
}

export interface StoriesResponse {
  stories: StoryLogEntry[];
  total: number;
  limit: number;
  offset: number;
}
```

- [ ] **Step 2: Add admin API functions to client.ts**

In `frontend/src/api/client.ts`, add the import for new types at the top:

```typescript
import type {
  KidProfile,
  Genre,
  HistoricalEvent,
  JobCreatedResponse,
  JobStatusResponse,
  JobCompleteResponse,
  AdminMe,
  AllowedEmail,
  StoryDetail,
  StoriesResponse,
} from "../types";
```

Add these functions at the end of the file:

```typescript

// Admin API

export async function fetchAdminMe(): Promise<AdminMe> {
  const res = await fetch(`${BASE}/admin/me`, { headers: authHeaders() });
  return handleResponse(res);
}

export async function fetchAllowedEmails(): Promise<AllowedEmail[]> {
  const res = await fetch(`${BASE}/admin/emails`, { headers: authHeaders() });
  const data = await handleResponse<{ emails: AllowedEmail[] }>(res);
  return data.emails;
}

export async function addAllowedEmail(email: string): Promise<void> {
  const res = await fetch(`${BASE}/admin/emails`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ email }),
  });
  await handleResponse(res);
}

export async function removeAllowedEmail(email: string): Promise<void> {
  const res = await fetch(`${BASE}/admin/emails/${encodeURIComponent(email)}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  await handleResponse(res);
}

export async function fetchStories(limit = 20, offset = 0): Promise<StoriesResponse> {
  const res = await fetch(`${BASE}/admin/stories?limit=${limit}&offset=${offset}`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export async function fetchStory(id: number): Promise<StoryDetail> {
  const res = await fetch(`${BASE}/admin/stories/${id}`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/api/client.ts
git commit -m "feat: add admin API types and client functions"
```

---

### Task 7: Build AdminScreen component

**Files:**
- Create: `frontend/src/components/AdminScreen.tsx`

- [ ] **Step 1: Create AdminScreen.tsx**

```tsx
import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import type { AllowedEmail, StoryLogEntry, StoryDetail } from "../types";
import {
  fetchAllowedEmails,
  addAllowedEmail,
  removeAllowedEmail,
  fetchStories,
  fetchStory,
} from "../api/client";

interface AdminScreenProps {
  onBack: () => void;
}

type Tab = "emails" | "stories";

export default function AdminScreen({ onBack }: AdminScreenProps) {
  const [tab, setTab] = useState<Tab>("stories");

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2
          className="text-2xl font-bold text-ethereal"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Admin
        </h2>
        <button
          onClick={onBack}
          className="text-starlight/50 hover:text-starlight transition-colors text-sm"
        >
          &larr; Back to app
        </button>
      </div>

      <div className="flex gap-2 mb-6">
        {(["stories", "emails"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                : "text-starlight/50 hover:text-starlight/80"
            }`}
          >
            {t === "emails" ? "Allowed Emails" : "Story Log"}
          </button>
        ))}
      </div>

      {tab === "emails" ? <EmailsTab /> : <StoriesTab />}
    </div>
  );
}

function EmailsTab() {
  const [emails, setEmails] = useState<AllowedEmail[]>([]);
  const [newEmail, setNewEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const data = await fetchAllowedEmails();
      setEmails(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load emails");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail.trim()) return;
    setError("");
    try {
      await addAllowedEmail(newEmail.trim());
      setNewEmail("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add email");
    }
  };

  const handleRemove = async (email: string) => {
    setError("");
    try {
      await removeAllowedEmail(email);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove email");
    }
  };

  if (loading) return <p className="text-starlight/50">Loading...</p>;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <form onSubmit={handleAdd} className="flex gap-2">
        <input
          type="email"
          value={newEmail}
          onChange={(e) => setNewEmail(e.target.value)}
          placeholder="user@gmail.com"
          className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-starlight placeholder-starlight/30 focus:outline-none focus:border-purple-400/50 text-sm"
        />
        <button
          type="submit"
          disabled={!newEmail.trim()}
          className="px-4 py-2 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/30 text-sm font-medium hover:bg-purple-500/30 disabled:opacity-50 transition-colors"
        >
          Add
        </button>
      </form>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left px-4 py-3 text-starlight/50 font-medium">Email</th>
              <th className="text-left px-4 py-3 text-starlight/50 font-medium">Added</th>
              <th className="px-4 py-3 w-16"></th>
            </tr>
          </thead>
          <tbody>
            {emails.map((e) => (
              <tr key={e.id} className="border-b border-white/5 hover:bg-white/5">
                <td className="px-4 py-3 text-starlight">{e.email}</td>
                <td className="px-4 py-3 text-starlight/50">
                  {new Date(e.added_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleRemove(e.email)}
                    className="text-red-400/60 hover:text-red-400 transition-colors text-xs"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
            {emails.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-6 text-center text-starlight/30">
                  No emails in allowlist
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}

function StoriesTab() {
  const [stories, setStories] = useState<StoryLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);
  const [detail, setDetail] = useState<StoryDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const limit = 20;

  const load = useCallback(async (off: number) => {
    setLoading(true);
    try {
      const data = await fetchStories(limit, off);
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
      const d = await fetchStory(id);
      setDetail(d);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading && stories.length === 0) return <p className="text-starlight/50">Loading...</p>;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      {error && <p className="text-red-400 text-sm">{error}</p>}

      <p className="text-starlight/40 text-xs">{total} stories total</p>

      <div className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left px-3 py-3 text-starlight/50 font-medium">Date</th>
              <th className="text-left px-3 py-3 text-starlight/50 font-medium">User</th>
              <th className="text-left px-3 py-3 text-starlight/50 font-medium">Kid</th>
              <th className="text-left px-3 py-3 text-starlight/50 font-medium">Type</th>
              <th className="text-left px-3 py-3 text-starlight/50 font-medium">Title</th>
            </tr>
          </thead>
          <tbody>
            {stories.map((s) => (
              <>
                <tr
                  key={s.id}
                  onClick={() => handleExpand(s.id)}
                  className="border-b border-white/5 hover:bg-white/5 cursor-pointer"
                >
                  <td className="px-3 py-3 text-starlight/60 whitespace-nowrap">
                    {new Date(s.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-3 py-3 text-starlight/60 truncate max-w-32">{s.user_email}</td>
                  <td className="px-3 py-3 text-starlight">
                    {s.kid_name}, {s.kid_age}
                  </td>
                  <td className="px-3 py-3 text-starlight/60">
                    {s.story_type === "custom" ? s.genre : s.event_id}
                  </td>
                  <td className="px-3 py-3 text-starlight truncate max-w-48">{s.title}</td>
                </tr>
                {expanded === s.id && (
                  <tr key={`${s.id}-detail`}>
                    <td colSpan={5} className="px-3 py-4 bg-white/5">
                      {detailLoading ? (
                        <p className="text-starlight/50 text-sm">Loading...</p>
                      ) : detail ? (
                        <div className="space-y-4 text-sm">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <span className="text-starlight/40">Mood:</span>{" "}
                              <span className="text-starlight">{detail.mood || "—"}</span>
                            </div>
                            <div>
                              <span className="text-starlight/40">Length:</span>{" "}
                              <span className="text-starlight">{detail.length || "—"}</span>
                            </div>
                            <div>
                              <span className="text-starlight/40">Duration:</span>{" "}
                              <span className="text-starlight">{detail.duration_seconds}s</span>
                            </div>
                            <div>
                              <span className="text-starlight/40">Description:</span>{" "}
                              <span className="text-starlight">{detail.description || "—"}</span>
                            </div>
                          </div>
                          <div>
                            <h4 className="text-starlight/40 mb-1">Prompt</h4>
                            <pre className="text-starlight/80 whitespace-pre-wrap bg-black/20 rounded-lg p-3 max-h-64 overflow-y-auto text-xs">
                              {detail.prompt}
                            </pre>
                          </div>
                          <div>
                            <h4 className="text-starlight/40 mb-1">Story</h4>
                            <pre className="text-starlight/80 whitespace-pre-wrap bg-black/20 rounded-lg p-3 max-h-64 overflow-y-auto text-xs">
                              {detail.story_text}
                            </pre>
                          </div>
                        </div>
                      ) : (
                        <p className="text-red-400 text-sm">Failed to load details</p>
                      )}
                    </td>
                  </tr>
                )}
              </>
            ))}
            {stories.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-starlight/30">
                  No stories generated yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {total > limit && (
        <div className="flex justify-center gap-2">
          <button
            disabled={offset === 0}
            onClick={() => load(Math.max(0, offset - limit))}
            className="px-3 py-1 rounded text-sm text-starlight/50 hover:text-starlight disabled:opacity-30 transition-colors"
          >
            &larr; Prev
          </button>
          <span className="text-starlight/40 text-sm py-1">
            {offset + 1}–{Math.min(offset + limit, total)} of {total}
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
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/AdminScreen.tsx
git commit -m "feat: add AdminScreen component with email and story tabs"
```

---

### Task 8: Wire AdminScreen into App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add admin state and imports**

In `frontend/src/App.tsx`, add imports:

```typescript
import AdminScreen from "./components/AdminScreen";
import { fetchAdminMe } from "./api/client";
```

Add to the existing imports from `./api/client` — merge `fetchAdminMe` into the existing import block.

- [ ] **Step 2: Add admin state variables**

Inside the `App` component, after the `const [authenticated, setAuthenticated] = useState(...)` line (line 61), add:

```typescript
  const [isAdmin, setIsAdmin] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
```

- [ ] **Step 3: Check admin status after login**

Add a `useEffect` after the existing `useEffect` for polling resume (around line 119):

```typescript
  useEffect(() => {
    if (authenticated) {
      fetchAdminMe()
        .then((me) => setIsAdmin(me.is_admin))
        .catch(() => setIsAdmin(false));
    }
  }, [authenticated]);
```

- [ ] **Step 4: Add admin button to header**

In the `<header>` section (around line 177-186), add after the closing `</p>` of the subtitle:

```tsx
          {isAdmin && (
            <button
              onClick={() => setShowAdmin(!showAdmin)}
              className="mt-2 text-xs text-starlight/30 hover:text-starlight/60 transition-colors"
            >
              {showAdmin ? "Close Admin" : "Admin"}
            </button>
          )}
```

- [ ] **Step 5: Show AdminScreen when toggled**

In the `<main>` section, wrap the existing content. After the error display block and before `<AnimatePresence mode="wait">` (around line 200), add:

```tsx
          {showAdmin ? (
            <AdminScreen onBack={() => setShowAdmin(false)} />
          ) : (
```

And after the closing `</AnimatePresence>` tag (around line 243), add:

```tsx
          )}
```

- [ ] **Step 6: Start dev server and verify**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173 — verify:
- The app loads normally
- No "Admin" button visible (since no admin emails configured locally)
- All existing flows still work

- [ ] **Step 7: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: wire AdminScreen into app with admin role check"
```

---

### Task 9: Update environment and deploy

**Files:**
- Modify: `backend/app/config.py` (already done in Task 1)
- Modify: `CLAUDE.md` (update env var docs)

- [ ] **Step 1: Update CLAUDE.md**

In the Backend (Render) environment variables section, add:

```
DATABASE_URL=                    # Auto-set by Render when linking Postgres
ADMIN_EMAILS=                    # Comma-separated admin email addresses
```

- [ ] **Step 2: Set env vars on Render**

In the Render dashboard for `taleweaver-api`, add:
- `ADMIN_EMAILS` = your admin email address

`DATABASE_URL` should be auto-injected when the Postgres instance is linked.

- [ ] **Step 3: Push to deploy**

```bash
git push origin main
```

Both Vercel (frontend) and Render (backend) will auto-deploy.

- [ ] **Step 4: Verify deployment**

After deploy completes:
1. Visit the app and sign in with your admin email
2. Verify the "Admin" button appears in the header
3. Click Admin → Emails tab → verify your seeded emails appear
4. Generate a test story → go to Admin → Stories tab → verify the story is logged with prompt and full text
5. Add/remove an email via the admin panel and verify it works

- [ ] **Step 5: Commit CLAUDE.md update**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with database and admin env vars"
git push origin main
```
